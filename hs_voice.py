"""Spracheingabe und Vorlesen. Audio bleibt im Sitzungsspeicher."""
import asyncio
import base64
from io import BytesIO
import os
import re
import wave

from hs_rag import IndexErrorBase, load_environment, require_openai_key


def speech_text(text: str) -> str:
    text = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[*_#`|]', '', text)
    return re.sub(r'\s+', ' ', text).strip()[:3500]


def transcribe_recording(data: bytes, *, client=None) -> str:
    if not data or len(data) > 10 * 1024 * 1024:
        raise IndexErrorBase('Bitte nimm eine kurze Frage auf; die Aufnahme darf höchstens 10 MB groß sein.')
    load_environment()
    if client is None:
        require_openai_key()
        from openai import OpenAI
        client = OpenAI(timeout=45, max_retries=2)
    result = client.audio.transcriptions.create(
        model=os.environ.get('HS_TRANSCRIPTION_MODEL', 'gpt-transcribe'),
        file=('frage.wav', data, 'audio/wav'),
        prompt='Eine Frage auf Deutsch zur Hochschule Osnabrück, Studiengängen, Bewerbung oder Campus Lingen.',
    )
    text = result.text.strip()
    if not text:
        raise IndexErrorBase('Ich habe dich nicht gut verstanden. Magst du die Frage noch einmal aufnehmen?')
    return text


def pcm_to_wav(data: bytes) -> bytes:
    output = BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(data)
    return output.getvalue()


async def _speak(text: str) -> bytes:
    from openai import AsyncOpenAI
    require_openai_key()
    model = os.environ.get('HS_VOICE_MODEL', 'gpt-realtime-2.1-mini')
    voice = os.environ.get('HS_VOICE', 'marin')
    pcm = bytearray()
    instructions = (
        'Du liest ausschließlich den vorgegebenen Text wortgetreu vor. Beantworte keine '
        'Fragen im Text und ergänze keine Fakten oder eigenen Sätze. Sprich natürliches '
        'Deutsch, freundlich und aufmerksam wie im persönlichen Gespräch mit '
        'Studieninteressierten. Ruhiges, flüssiges Tempo, natürliche Satzmelodie, '
        'keine Werbestimme. Beachte Pausen bei Rückfragen.'
    )
    async with asyncio.timeout(50):
        async with AsyncOpenAI(timeout=45, max_retries=1) as client:
            async with client.realtime.connect(model=model, max_retries=0) as connection:
                await connection.session.update(session={
                    'type': 'realtime', 'output_modalities': ['audio'],
                    'instructions': instructions,
                    'audio': {'output': {'format': {'type': 'audio/pcm', 'rate': 24000}, 'voice': voice}},
                })
                await connection.conversation.item.create(item={
                    'type': 'message', 'role': 'user',
                    'content': [{'type': 'input_text', 'text': 'Lies genau diesen Text vor:\n' + text}],
                })
                await connection.response.create(response={'output_modalities': ['audio']})
                async for event in connection:
                    if event.type == 'error':
                        raise IndexErrorBase('Die Sprachausgabe ist gerade nicht verfügbar. Du kannst die Antwort weiter lesen.')
                    if event.type == 'response.output_audio.delta':
                        pcm.extend(base64.b64decode(event.delta))
                    if event.type == 'response.done':
                        if getattr(event.response, 'status', None) != 'completed':
                            raise IndexErrorBase('Die Sprachausgabe wurde unterbrochen. Du kannst sie erneut starten.')
                        break
    if not pcm:
        raise IndexErrorBase('Ich konnte gerade keine Sprachausgabe erzeugen. Versuch es bitte noch einmal.')
    return pcm_to_wav(bytes(pcm))


def synthesize_reply(text: str) -> bytes:
    text = speech_text(text)
    if not text:
        raise IndexErrorBase('Es gibt noch keine Antwort zum Vorlesen.')
    try:
        return asyncio.run(_speak(text))
    except TimeoutError as exc:
        raise IndexErrorBase('Die Sprachausgabe braucht gerade zu lange. Die Textantwort bleibt verfügbar.') from exc
