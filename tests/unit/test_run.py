import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import importlib

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import run
from run import create_app, make_shell_context

class TestRun(unittest.TestCase):

    @patch('run.load_dotenv')
    @patch('run.os.getenv')
    @patch('app.utils.ollama_client.os.getenv')
    def test_create_app(self, mock_ollama_getenv, mock_getenv, mock_load_dotenv):
        mock_getenv.side_effect = {
            'FLASK_ENV': 'testing',
            'SECRET_KEY': 'test_secret_key',
            'DATABASE_URL': 'sqlite:///:memory:',
            'DEBUG': 'False',
            'FLASK_PORT': '5000',
            'RSS_CHECK_INTERVAL': '30',
            'SUMMARY_CHECK_INTERVAL': '60',
            'SUMMARY_API_CHOICE': 'groq'
        }.get
        mock_ollama_getenv.side_effect = {
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'OLLAMA_MODEL': 'llama2'
        }.get
        app = create_app()
        self.assertIsNotNone(app)
        self.assertEqual(app.config['FLASK_ENV'], 'testing')
        mock_load_dotenv.assert_called_once()

    @patch('run.db')
    @patch('run.User')
    def test_make_shell_context(self, mock_User, mock_db):
        context = make_shell_context()
        self.assertIn('db', context)
        self.assertIn('User', context)
        self.assertEqual(context['db'], mock_db)
        self.assertEqual(context['User'], mock_User)

    @patch('run.create_app')
    @patch('run.os.getenv')
    @patch('app.utils.ollama_client.os.getenv')
    def test_main_run(self, mock_ollama_getenv, mock_getenv, mock_create_app):
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        mock_getenv.side_effect = {
            'FLASK_PORT': '5000',
            'FLASK_ENV': 'development',
            'SECRET_KEY': 'test_secret_key',
            'DATABASE_URL': 'sqlite:///:memory:',
            'DEBUG': 'True',
            'RSS_CHECK_INTERVAL': '30',
            'SUMMARY_CHECK_INTERVAL': '60',
            'SUMMARY_API_CHOICE': 'groq'
        }.get
        mock_ollama_getenv.side_effect = {
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'OLLAMA_MODEL': 'llama2'
        }.get

        with patch('run.__name__', '__main__'):
            import importlib
            importlib.reload(run)
            mock_app.run.assert_called_once_with(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    unittest.main()
