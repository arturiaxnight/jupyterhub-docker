# JupyterHub configuration
#
# If you update this file, remove the jupyterhub_data volume before restarting:
#
#     docker volume rm jupyterhub_jupyterhub_data
#
# or, if COMPOSE_PROJECT_NAME is <name>:
#
#     docker volume rm <name>_jupyterhub_data

import os
import sys

from docker.types import DeviceRequest

c = get_config()  # noqa: F821

## Generic
c.JupyterHub.admin_access = True
c.Spawner.default_url = "/lab"

## Authenticator — NativeAuthenticator (self-service signup)
c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"
c.Authenticator.allow_all = True

# False (default): signup needs admin approval at /hub/authorize before login/spawn.
# True: anyone who signs up can log in immediately.
c.NativeAuthenticator.open_signup = (
    os.environ.get("OPEN_SIGNUP", "false").lower() in ("1", "true", "yes")
)
c.NativeAuthenticator.enable_signup = (
    os.environ.get("ENABLE_SIGNUP", "true").lower() in ("1", "true", "yes")
)

admin = os.environ.get("JUPYTERHUB_ADMIN")
if admin:
    c.Authenticator.admin_users = {admin}

## DockerSpawner — each user gets an isolated container
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
c.DockerSpawner.image = os.environ["DOCKER_NOTEBOOK_IMAGE"]
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = os.environ["DOCKER_NETWORK_NAME"]
c.DockerSpawner.remove = True
c.DockerSpawner.debug = True

# Bind Hub API on all interfaces; user containers connect via container name on the Docker network
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = os.environ.get("HUB_IP", "jupyterhub")
c.JupyterHub.hub_port = 8080

# User data persistence
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
c.DockerSpawner.notebook_dir = notebook_dir
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": notebook_dir}

# Resource limits (adjust for your host)
c.Spawner.cpu_limit = float(os.environ.get("CPU_LIMIT", "4"))
c.Spawner.mem_limit = os.environ.get("MEM_LIMIT", "16G")

# Expose host NVIDIA GPUs to user containers (requires nvidia-container-toolkit)
if os.environ.get("ENABLE_GPU", "true").lower() in ("1", "true", "yes"):
    c.DockerSpawner.extra_host_config = {
        "device_requests": [
            DeviceRequest(
                count=int(os.environ.get("GPU_COUNT", "-1")),
                capabilities=[["gpu"]],
            )
        ]
    }

# Persist hub database and cookie secret
c.JupyterHub.cookie_secret_file = "/data/jupyterhub_cookie_secret"
c.JupyterHub.db_url = "sqlite:////data/jupyterhub.sqlite"

# Bind Hub HTTP API / proxy on all interfaces inside the container
c.JupyterHub.bind_url = "http://:8000"

# When behind an HTTPS reverse proxy, set PUBLIC_URL (e.g. https://jupyter.example.com)
public_url = os.environ.get("PUBLIC_URL")
if public_url:
    c.JupyterHub.public_url = public_url

## Cull idle servers
c.JupyterHub.services = [
    {
        "name": "idle-culler",
        "command": [
            sys.executable,
            "-m",
            "jupyterhub_idle_culler",
            f"--timeout={os.environ.get('CULL_TIMEOUT', '3600')}",
        ],
    }
]
c.JupyterHub.load_roles = [
    {
        "name": "idle-culler",
        "scopes": [
            "list:users",
            "read:users:activity",
            "read:servers",
            "delete:servers",
        ],
        "services": ["idle-culler"],
    }
]
