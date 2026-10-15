#!/bin/bash
set -euo pipefail

CONFIG=/srv/jupyterhub/jupyterhub_config.py

# Create NativeAuthenticator tables if needed, then ensure admin credentials exist.
python3 - <<'PY'
from sqlalchemy import create_engine
from nativeauthenticator.orm import Base

engine = create_engine("sqlite:////data/jupyterhub.sqlite")
Base.metadata.create_all(engine)
print("Ensured nativeauthenticator tables exist", flush=True)
PY

python3 /srv/jupyterhub/bootstrap_admin.py

exec jupyterhub -f "$CONFIG"
