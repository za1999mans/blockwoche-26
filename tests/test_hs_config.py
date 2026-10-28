"""Cloud-Konfiguration ohne echte Zugangsdaten oder API-Aufrufe prüfen."""
import os
import unittest
from unittest.mock import Mock, patch

from hs_rag import IndexErrorBase, OpenAIEmbeddings, load_environment
from hs_voice import synthesize_reply, transcribe_recording


class CloudConfigTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        dotenv = patch('dotenv.load_dotenv')
        dotenv.start()
        self.addCleanup(dotenv.stop)

    def test_cloud_secrets_reach_environment_used_by_all_clients(self):
        load_environment({'OPENAI_API_KEY': 'test-placeholder',
                          'HS_CHAT_MODEL': 'test-chat', 'HS_VOICE': 'test-voice'})
        self.assertEqual(os.environ['OPENAI_API_KEY'], 'test-placeholder')
        self.assertEqual(os.environ['HS_CHAT_MODEL'], 'test-chat')
        self.assertEqual(os.environ['HS_VOICE'], 'test-voice')

    def test_existing_environment_has_precedence(self):
        os.environ['OPENAI_API_KEY'] = 'existing-placeholder'
        load_environment({'OPENAI_API_KEY': 'cloud-placeholder'})
        self.assertEqual(os.environ['OPENAI_API_KEY'], 'existing-placeholder')

    def test_missing_local_secrets_file_allows_dotenv_fallback(self):
        secrets = Mock()
        secrets.get.side_effect = FileNotFoundError('No secrets.toml')
        load_environment(secrets)
        from dotenv import load_dotenv
        load_dotenv.assert_called_once()

    def test_nested_blank_and_unrelated_secrets_are_not_exported(self):
        load_environment({'OPENAI_API_KEY': '  ', 'HS_CHAT_MODEL': {'value': 'nested'},
                          'unrelated_password': 'unused'})
        self.assertNotIn('OPENAI_API_KEY', os.environ)
        self.assertNotIn('HS_CHAT_MODEL', os.environ)
        self.assertNotIn('unrelated_password', os.environ)

    def test_invalid_configuration_is_not_silently_ignored(self):
        secrets = Mock()
        secrets.get.side_effect = ValueError('Invalid TOML')
        with self.assertRaises(ValueError):
            load_environment(secrets)

    def test_missing_key_has_cloud_instructions_for_text_and_voice(self):
        calls = (
            lambda: OpenAIEmbeddings('test-model').client,
            lambda: transcribe_recording(b'test-audio'),
            lambda: synthesize_reply('Hallo!'),
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaisesRegex(IndexErrorBase, 'Settings → Secrets'):
                    call()


if __name__ == '__main__':
    unittest.main()
