"""Run from the repository root: python3 scripts/serve.py."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from emotion_lab.server import make_server

parser = argparse.ArgumentParser(description='Serve only the public research viewer on loopback.')
parser.add_argument('--port', type=int, default=8787)
args = parser.parse_args()
if not 1 <= args.port <= 65535:
    parser.error('port must be between 1 and 65535')
with make_server(args.port) as server:
    print(f'http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
