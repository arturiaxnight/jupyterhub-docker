ARG JUPYTERHUB_VERSION=5.2.1
FROM quay.io/jupyterhub/jupyterhub:${JUPYTERHUB_VERSION}

RUN python3 -m pip install --no-cache-dir \
    dockerspawner \
    jupyterhub-nativeauthenticator \
    jupyterhub-idle-culler \
    bcrypt

COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY bootstrap_admin.py /srv/jupyterhub/bootstrap_admin.py
COPY start.sh /srv/jupyterhub/start.sh
RUN chmod +x /srv/jupyterhub/start.sh /srv/jupyterhub/bootstrap_admin.py

CMD ["/srv/jupyterhub/start.sh"]
