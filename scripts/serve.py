"""Single-container lifecycle: Next public port, FastAPI loopback only."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    port=os.getenv('PORT','3000')
    if not port.isdigit() or not 1<=int(port)<=65535 or port=='8000':
        raise SystemExit('PORT must be a valid port other than the internal backend port 8000')
    children=[]
    def shutdown(*_):
        for child in children:
            if child.poll() is None:child.terminate()
    signal.signal(signal.SIGTERM,shutdown)
    signal.signal(signal.SIGINT,shutdown)
    try:
        children.append(subprocess.Popen([sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000'],cwd=ROOT))
        env={**os.environ,'HOSTNAME':'0.0.0.0','PORT':port}
        children.append(subprocess.Popen(['node','frontend/server.js'],cwd=ROOT,env=env))
        while all(c.poll() is None for c in children):time.sleep(.25)
        return next(c.returncode for c in children if c.returncode is not None)
    finally:
        shutdown()
        for child in children:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait()

if __name__=='__main__':sys.exit(main())
