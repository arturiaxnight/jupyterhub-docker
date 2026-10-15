# Single-user JupyterLab image for physicians / researchers.
# Includes: Python (scipy), R (IRkernel), PyTorch (CUDA), TensorFlow (CUDA).
FROM quay.io/jupyter/pytorch-notebook:cuda12-latest

LABEL maintainer="jupyterhub-docker"

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fonts-dejavu \
        git \
        vim \
        libicu-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# R for JupyterLab (physicians / biostats)
RUN mamba install --quiet --yes \
        'r-base' \
        'r-essentials' \
        'r-irkernel' \
        'r-tidyverse' \
        'r-shiny' \
        'r-rmarkdown' \
        'r-caret' \
        'r-randomforest' \
        'r-survival' \
        'r-survminer' \
        'r-ggplot2' \
        'r-data.table' \
    && mamba clean --all -f -y \
    && fix-permissions "${CONDA_DIR}" \
    && fix-permissions "/home/${NB_USER}"

# TensorFlow with CUDA (PyTorch already provided by base image)
RUN pip install --no-cache-dir \
        'tensorflow[and-cuda]' \
        jupyterlab-git \
    && fix-permissions "${CONDA_DIR}" \
    && fix-permissions "/home/${NB_USER}"

COPY ./conda-activate.sh /usr/local/bin/before-notebook.d/conda-activate.sh
COPY ./overrides.json /opt/conda/share/jupyter/lab/settings/overrides.json
USER root
RUN chmod +x /usr/local/bin/before-notebook.d/conda-activate.sh \
    && fix-permissions /opt/conda/share/jupyter/lab/settings
USER ${NB_UID}
