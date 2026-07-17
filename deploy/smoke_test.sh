#!/bin/sh
set -eu
BASE_URL=${SMOKE_BASE_URL:-http://127.0.0.1}
python - "$BASE_URL" <<'PY'
import sys,time,urllib.request
base=sys.argv[1].rstrip('/')
for path in ('/health/','/health/ready/','/conta/login/'):
    for attempt in range(12):
        try:
            with urllib.request.urlopen(base+path, timeout=5) as response:
                if response.status < 400: break
        except Exception:
            if attempt == 11: raise
            time.sleep(5)
    print(f'OK {path}')
PY
