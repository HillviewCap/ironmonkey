import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from run import create_app, make_shell_context

class TestRun(unittest.TestCase):

    @patch('run.load_dotenv')
    @patch('run.os.getenv')
    def test_create_app(self, mock_getenv, mock_load_dotenv):
        mock_getenv.return_value = 'testing'
        app = create_app()
        self.assertIsNotNone(app)
        self.assertEqual(app.config['ENV'], 'testing')
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
    def test_main_run(self, mock_getenv, mock_create_app):
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        mock_getenv.side_effect = ['development', '5000']

        with patch('run.__name__', '__main__'):
            import importlib
            importlib.reload(run)
            mock_app.run.assert_called_once_with(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    unittest.main()
