#!/usr/bin/env python3
"""Apply and verify Dograh's Speechify aiohttp proxy fix."""

from pathlib import Path

target = Path("/app/api/services/pipecat/service_factory.py")

if not target.is_file():
    raise SystemExit(f"ERROR: source file not found: {target}")

source = target.read_text()

old = "session = aiohttp.ClientSession()"
new = "session = aiohttp.ClientSession(trust_env=True)"

old_count = source.count(old)
new_count = source.count(new)

if old_count == 1 and new_count == 0:
    updated = source.replace(old, new, 1)
elif old_count == 0 and new_count == 1:
    updated = source
else:
    raise SystemExit(
        "ERROR: Unexpected upstream source. "
        f"Original occurrences={old_count}, patched occurrences={new_count}. "
        "Refusing to modify the file."
    )

if new not in updated:
    raise SystemExit("ERROR: Patch verification failed.")

target.write_text(updated)
print(f"SUCCESS: Speechify proxy fix applied to {target}")