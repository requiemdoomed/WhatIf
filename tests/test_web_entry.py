"""Main HTML routing and cross-platform launcher checks."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from app import create_app, ROOT
import run


class WebEntryTests(unittest.TestCase):
    def test_both_addresses_serve_the_main_file(self):
        with tempfile.TemporaryDirectory() as folder:
            client = create_app(Path(folder)/'test.sqlite3', testing=True).test_client()
            for address in ('/', '/index.html'):
                response = client.get(address)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, (ROOT/'index.html').read_bytes())
                self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
                response.close()
            response=client.get('/static/js/entry.js')
            self.assertEqual(response.status_code,200);response.close()

    def test_html_keeps_local_instructions_and_relative_assets(self):
        html=(ROOT/'index.html').read_text()
        for text in ('static/js/entry.js', 'static/js/theme.js', 'static/css/style.css',
                     'START_WINDOWS.bat', 'START_MAC_LINUX.sh', 'whatif_notebook.ipynb'):
            self.assertIn(text,html)
        self.assertNotIn('src="/static/',html)

    def test_platform_environment_paths(self):
        root=Path('/project with spaces')
        self.assertEqual(run.environment_python(root,'win32'),root/'.venv/Scripts/python.exe')
        for platform in ('darwin','linux'):
            self.assertEqual(run.environment_python(root,platform),root/'.venv/bin/python')

    @patch('run.subprocess.call',return_value=0)
    @patch('run.prepare',return_value=Path('/project with spaces/python'))
    def test_default_start_opens_browser(self,prepare,call):
        self.assertEqual(run.main([]),0)
        prepare.assert_called_once_with(False)
        command=call.call_args.args[0]
        self.assertEqual(command[0],'/project with spaces/python')
        self.assertIn('--open-browser',command)
        self.assertIn(str(ROOT/'app.py'),command)

    @patch('run.subprocess.call',return_value=0)
    @patch('run.prepare',return_value=Path('/python'))
    def test_custom_port_without_browser(self,prepare,call):
        self.assertEqual(run.main(['--port','5051','--no-browser']),0)
        command=call.call_args.args[0]
        self.assertNotIn('--open-browser',command)
        self.assertEqual(command[-2:],['--port','5051'])

    @patch('run.subprocess.call',return_value=0)
    @patch('run.prepare',return_value=Path('/python'))
    def test_notebook_uses_original_file(self,prepare,call):
        self.assertEqual(run.main(['--notebook','--no-browser']),0)
        prepare.assert_called_once_with(True)
        self.assertEqual(call.call_args.args[0],['/python','-m','notebook',str(ROOT/'whatif_notebook.ipynb'),'--no-browser'])

    @patch('run.prepare',side_effect=subprocess.CalledProcessError(1,['pip']))
    def test_failed_setup_returns_failure(self,prepare):
        self.assertEqual(run.main([]),1)

    @patch('run.prepare')
    def test_invalid_port_does_not_create_environment(self,prepare):
        with self.assertRaises(SystemExit):run.main(['--port','70000'])
        prepare.assert_not_called()

if __name__=='__main__':unittest.main()
