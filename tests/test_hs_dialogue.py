from io import BytesIO
from types import SimpleNamespace
import unittest
import wave

from hs_dialogue import plan_turn
from hs_rag import IndexErrorBase, answer_question
from hs_voice import pcm_to_wav, speech_text, transcribe_recording


CATALOG = [
    {'name': 'Informatik (B.Sc.)', 'degree': 'B.Sc.', 'campus': 'Osnabrück, Westerberg'},
    {'name': 'Informatik (M.Sc.)', 'degree': 'M.Sc.', 'campus': 'Osnabrück, Westerberg'},
    {'name': 'Informatik – Technische Informatik (B.Sc.)', 'degree': 'B.Sc.', 'campus': 'Osnabrück, Westerberg'},
    {'name': 'Hebammenwissenschaft (B.Sc.), dual', 'degree': 'B.Sc.', 'campus': 'Osnabrück, Caprivi'},
    {'name': 'Soziale Arbeit (B.A.)', 'degree': 'B.A.', 'campus': 'Osnabrück, Caprivi'},
    {'name': 'Betriebswirtschaft und Management (B.A.)', 'degree': 'B.A.', 'campus': 'Osnabrück, Caprivi'},
    {'name': 'Betriebswirtschaft und Management (B.A.), Standort Lingen (Ems)', 'degree': 'B.A.', 'campus': 'Lingen'},
]


class NoSearchIndex:
    programme_catalog = CATALOG

    def search(self, *args, **kwargs):
        raise AssertionError('Für diese Gesprächswendung darf keine Wissenssuche laufen')


class DialogueTests(unittest.TestCase):
    def test_hallo_is_a_greeting_without_retrieval(self):
        reply = answer_question('hallo', NoSearchIndex())
        self.assertEqual(reply['kind'], 'greeting')
        self.assertIn('Hallo', reply['answer'])
        self.assertIn('?', reply['answer'])
        self.assertEqual(reply['sources'], [])
        self.assertNotIn('Belege', reply['answer'])

    def test_screenshot_semester_question_cannot_invent_a_programme(self):
        reply = answer_question('wie viele Semester sind hier geplant?', NoSearchIndex(), history=[
            {'role': 'user', 'content': 'hallo'},
            {'role': 'assistant', 'content': 'Hallo!'},
        ])
        self.assertEqual(reply['kind'], 'clarification')
        self.assertIsNone(reply['dialogue_state']['programme'])
        self.assertNotIn('Hebammen', reply['answer'])
        self.assertNotIn('7', reply['answer'])

    def test_previous_hallucination_is_not_a_user_choice(self):
        reply = answer_question('Wie viele Semester sind hier geplant?', NoSearchIndex(), history=[
            {'role': 'user', 'content': 'hallo'},
            {'role': 'assistant', 'content': 'Hebammenwissenschaft dauert 7 Semester.'},
        ])
        self.assertEqual(reply['kind'], 'clarification')

    def test_informatik_asks_bachelor_or_master(self):
        turn = plan_turn('Ich interessiere mich für Informatik', CATALOG)
        self.assertEqual(turn.kind, 'clarification')
        self.assertIn('Bachelor', turn.answer)
        self.assertEqual(len(turn.state['candidates']), 2)

    def test_clarification_preserves_original_semester_question(self):
        first = plan_turn('Wie viele Semester dauert das?', CATALOG)
        second = plan_turn('Informatik', CATALOG, state=first.state)
        third = plan_turn('Bachelor', CATALOG, state=second.state)
        self.assertEqual(third.kind, 'knowledge')
        self.assertEqual(third.scope['programme'], 'Informatik (B.Sc.)')
        self.assertIn('Wie viele Semester dauert das?', third.query)

    def test_followup_reuses_explicitly_chosen_programme(self):
        turn = plan_turn('Und welche Module gibt es dort?', CATALOG,
                         state={'programme': 'Informatik (B.Sc.)'})
        self.assertEqual(turn.scope['programme'], 'Informatik (B.Sc.)')
        self.assertIn('Informatik (B.Sc.)', turn.query)

    def test_explicit_programme_switch_replaces_previous_choice(self):
        turn = plan_turn('Was lerne ich in Soziale Arbeit?', CATALOG,
                         state={'programme': 'Informatik (B.Sc.)'})
        self.assertEqual(turn.scope['programme'], 'Soziale Arbeit (B.A.)')

    def test_new_question_does_not_reuse_old_pending_question(self):
        turn = plan_turn('Wie bewerbe ich mich für Soziale Arbeit?', CATALOG,
                         state={'pending_question': 'Wie viele Semester?', 'programme': None})
        self.assertNotIn('Wie viele Semester?', turn.query)

    def test_specialisation_is_more_specific_than_generic_informatik(self):
        turn = plan_turn('Welche Module hat Technische Informatik?', CATALOG)
        self.assertEqual(turn.scope['programme'], 'Informatik – Technische Informatik (B.Sc.)')

    def test_same_degree_different_city_asks_which_offer(self):
        turn = plan_turn('Betriebswirtschaft und Management', CATALOG)
        self.assertEqual(turn.kind, 'clarification')
        resolved = plan_turn('in Lingen', CATALOG, state=turn.state)
        self.assertIn('Lingen', resolved.scope['programme'])

    def test_unknown_state_cannot_add_a_programme_to_catalog(self):
        turn = plan_turn('Wie viele Semester?', CATALOG, state={'programme': 'Erfundenes Studium'})
        self.assertEqual(turn.kind, 'clarification')

    def test_degree_switch_can_resolve_master_of_same_subject(self):
        turn = plan_turn('Und im Master?', CATALOG, state={'programme': 'Informatik (B.Sc.)'})
        self.assertEqual(turn.scope['programme'], 'Informatik (M.Sc.)')

    def test_sidebar_selection_is_used(self):
        turn = plan_turn('Wie viele Semester?', CATALOG, programme='Soziale Arbeit (B.A.)')
        self.assertEqual(turn.scope['programme'], 'Soziale Arbeit (B.A.)')

    def test_orientation_is_a_conversation_without_unverified_advice(self):
        reply = answer_question('Ich weiß es noch nicht', NoSearchIndex())
        self.assertEqual(reply['kind'], 'orientation')
        self.assertIn('?', reply['answer'])
        self.assertTrue(reply['suggestions'])

    def test_generic_nc_definition_does_not_require_programme(self):
        turn = plan_turn('Was bedeutet NC?', CATALOG)
        self.assertEqual(turn.kind, 'knowledge')

    def test_interest_button_explores_instead_of_selecting_informatik(self):
        turn = plan_turn('Technik und Informatik', CATALOG)
        self.assertEqual(turn.kind, 'orientation')
        self.assertIsNone(turn.state['programme'])
        followup = plan_turn('Software entwickeln', CATALOG, state=turn.state)
        self.assertIn('Technik und Informatik', followup.query)

    def test_comparison_does_not_choose_one_programme(self):
        turn = plan_turn('Was ist der Unterschied zwischen Informatik und Soziale Arbeit?', CATALOG,
                         state={'programme': 'Informatik (B.Sc.)'})
        self.assertEqual(turn.kind, 'knowledge')
        self.assertIsNone(turn.scope['programme'])
        followup = plan_turn('Welche Inhalte unterscheiden sich?', CATALOG, state=turn.state)
        self.assertIsNone(followup.scope['programme'])
        self.assertIn('Soziale Arbeit', followup.query)
        self.assertIn('Informatik', followup.query)

    def test_explicit_campus_of_new_question_takes_precedence(self):
        turn = plan_turn('Betriebswirtschaft und Management in Lingen', CATALOG, campus='Osnabrück')
        self.assertIn('Lingen', turn.scope['programme'])

    def test_thanks_does_not_trigger_retrieval(self):
        self.assertEqual(answer_question('Danke!', NoSearchIndex())['kind'], 'smalltalk')

    def test_explicit_greeting_plus_question_still_answers_question(self):
        turn = plan_turn('Hallo, wie viele Semester dauert Soziale Arbeit?', CATALOG)
        self.assertEqual(turn.kind, 'knowledge')
        self.assertEqual(turn.scope['programme'], 'Soziale Arbeit (B.A.)')


class VoiceTests(unittest.TestCase):
    def test_citations_and_urls_are_not_read_aloud(self):
        text = '**Hallo!** Siehe [Campus](https://www.hs-osnabrueck.de/) [1][2].'
        spoken = speech_text(text)
        self.assertIn('Campus', spoken)
        self.assertNotIn('https', spoken)
        self.assertNotIn('[1]', spoken)
        self.assertNotIn('*', spoken)

    def test_audio_has_browser_playable_wav_header(self):
        audio = pcm_to_wav(b'\x00\x00' * 240)
        with wave.open(BytesIO(audio), 'rb') as wav:
            self.assertEqual(wav.getframerate(), 24000)
            self.assertEqual(wav.getnchannels(), 1)
            self.assertEqual(wav.getsampwidth(), 2)
            self.assertEqual(wav.getnframes(), 240)

    def test_recording_is_sent_as_named_wav_and_transcript_returned(self):
        calls = []

        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text='Hallo, ich interessiere mich für Informatik.')

        client = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create)))
        text = transcribe_recording(pcm_to_wav(b'\x00\x00' * 240), client=client)
        self.assertIn('Informatik', text)
        self.assertEqual(calls[0]['file'][0], 'frage.wav')
        self.assertEqual(calls[0]['file'][2], 'audio/wav')

    def test_empty_recording_is_not_sent(self):
        with self.assertRaises(IndexErrorBase):
            transcribe_recording(b'')
