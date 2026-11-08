FROM ghcr.io/speaches-ai/speaches:latest-cpu

# Temporarily become root to patch the installed application.
USER root

RUN python3 - <<'PY'
from pathlib import Path

path = Path("/home/ubuntu/speaches/src/speaches/ui/utils.py")
source = path.read_text()

old = 'headers={"Authorization": f"Bearer {config.api_key}"} if config.api_key else None,'
new = 'headers={"Authorization": f"Bearer {config.api_key.get_secret_value()}"} if config.api_key else None,'

count = source.count(old)
if count != 1:
    raise SystemExit(f"Expected exactly one matching line; found {count}. Aborting.")

path.write_text(source.replace(old, new, 1))
print("Successfully patched http_client_from_gradio_req")
PY

# Restore the original runtime user.
USER ubuntu
