#!/usr/bin/env python3
"""Ensure the configured admin account exists with a known password."""

import os
import sys

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nativeauthenticator.orm import UserInfo


def main() -> int:
    username = os.environ.get("JUPYTERHUB_ADMIN", "admin").strip()
    password = os.environ.get("JUPYTERHUB_ADMIN_PASSWORD", "").strip()
    db_url = os.environ.get("JUPYTERHUB_DB_URL", "sqlite:////data/jupyterhub.sqlite")

    if not password:
        print("JUPYTERHUB_ADMIN_PASSWORD not set; skip admin bootstrap", flush=True)
        return 0

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        user = session.query(UserInfo).filter_by(username=username).first()
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        if user is None:
            session.add(
                UserInfo(
                    username=username,
                    password=hashed,
                    is_authorized=True,
                )
            )
            session.commit()
            print(f"Created authorized admin user: {username}", flush=True)
        else:
            user.password = hashed
            user.is_authorized = True
            session.commit()
            print(f"Updated admin user password/authorization: {username}", flush=True)
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
