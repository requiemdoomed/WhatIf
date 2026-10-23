"""Start the complete WhatIf project. Author: Swayam Shakya."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def environment_python(root=ROOT, platform=None):
    platform = sys.platform if platform is None else platform
    return root / '.venv' / ('Scripts/python.exe' if platform == 'win32' else 'bin/python')


def prepare(notebook=False):
    python = environment_python()
    if not python.is_file():
        print('Preparing the project environment…', flush=True)
        subprocess.run([sys.executable, '-m', 'venv', str(ROOT / '.venv')], check=True)
    packages = [('Flask', '3', 'Flask>=3.0,<4.0')]
    if notebook:
        packages.append(('notebook', '7', 'notebook>=7.0,<8.0'))
    for name, major, requirement in packages:
        check = subprocess.run([str(python), '-c',
            'import importlib.metadata,sys; sys.exit(importlib.metadata.version(sys.argv[1]).split(".")[0] != sys.argv[2])',
            name, major], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if check.returncode:
            print(f'Installing {name}. First-time setup needs internet access…', flush=True)
            subprocess.run([str(python), '-m', 'pip', 'install', requirement], check=True)
    return python


def main(argv=None):
    parser = argparse.ArgumentParser(description='Open WhatIf in your browser.')
    parser.add_argument('--port', type=int, default=5050)
    parser.add_argument('--no-browser', action='store_true', help='Print the game address without opening a browser.')
    parser.add_argument('--notebook', action='store_true', help='Open the original project notebook instead.')
    args = parser.parse_args(argv)
    if sys.version_info < (3, 10):
        print('Please install Python 3.10 or newer, then run the launcher again.')
        return 1
    if not 0 <= args.port <= 65535:
        parser.error('Port must be between 0 and 65535. Use 0 to select a free port.')
    try:
        python = prepare(args.notebook)
        if args.notebook:
            command = [str(python), '-m', 'notebook', str(ROOT / 'whatif_notebook.ipynb')]
            if args.no_browser:
                command.append('--no-browser')
        else:
            command = [str(python), str(ROOT / 'app.py'), '--port', str(args.port)]
            if not args.no_browser:
                command.append('--open-browser')
        print('Keep this terminal open. Press Ctrl+C here to stop.', flush=True)
        return subprocess.call(command, cwd=ROOT)
    except KeyboardInterrupt:
        return 0
    except (OSError, subprocess.CalledProcessError) as error:
        print(f'Startup could not finish: {error}')
        print('Check your Python installation and internet connection. See README.md for manual setup.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
