"""Live-Prüfung der Besucherkonversation, optional mit synthetischem Audio-Rundlauf."""
from io import BytesIO
import argparse
import json
import wave

from hs_rag import ROOT, VectorIndex, answer_question, friendly_error, load_environment
from hs_voice import synthesize_reply, transcribe_recording


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', action='store_true')
    args = parser.parse_args()
    load_environment()
    index = VectorIndex()
    history = []
    state = {}
    records = []
    questions = ['hallo', 'wie viele Semester sind hier geplant?', 'Informatik', 'Bachelor',
                 'Und welche Inhalte erwarten mich?']
    for question in questions:
        result = answer_question(question, index, history=history, dialogue_state=state)
        state = result['dialogue_state']
        history += [{'role': 'user', 'content': question}, {'role': 'assistant', 'content': result['answer']}]
        record = {'question': question, 'answer': result['answer'], 'kind': result['kind'],
                  'programme': state['programme'], 'source_count': len(result['sources'])}
        print(json.dumps(record, ensure_ascii=False), flush=True)
        records.append(record)
    assert [r['kind'] for r in records[:3]] == ['greeting', 'clarification', 'clarification']
    assert records[3]['programme'] == 'Informatik (B.Sc.)'
    assert '8' in records[3]['answer'] or 'acht' in records[3]['answer'].casefold()
    assert records[4]['programme'] == 'Informatik (B.Sc.)'
    assert records[4]['source_count'] > 0
    report = {'conversation': records, 'conversation_passed': True}
    (ROOT/'data/hs_dialogue_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    if args.audio:
        sample = 'Hallo! Für welchen Studiengang möchtest du die Semesterzahl wissen?'
        audio = synthesize_reply(sample)
        with wave.open(BytesIO(audio), 'rb') as wav:
            seconds = wav.getnframes() / wav.getframerate()
        transcript = transcribe_recording(audio)
        report['audio'] = {'seconds': round(seconds, 2), 'bytes': len(audio), 'transcript': transcript,
                           'passed': 'studiengang' in transcript.casefold() and 'semester' in transcript.casefold()}
        print(json.dumps({'audio': report['audio']}, ensure_ascii=False), flush=True)
        (ROOT/'data/hs_dialogue_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        if not report['audio']['passed']:
            return 1
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(friendly_error(exc), flush=True)
        raise SystemExit(1)
