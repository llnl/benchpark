FROM fluxrm/flux-core:el10

ARG TARGETARCH

USER root

RUN dnf clean all \
	&& rm -rf /var/cache/dnf \
	&& git config --global checkout.workers 1024 \
	&& git config --global feature.manyFiles true \
    && git config --global core.sharedRepository false \
	&& echo "* soft memlock unlimited" >> /etc/security/limits.conf \
    && echo "* hard memlock unlimited" >> /etc/security/limits.conf \
    && dnf install -y \
    xz \
    zstd \
    bzip2 \
    gettext \
    ncurses-devel \
    sqlite \
    pigz \
    libmd-devel \
    libbsd-devel \
    nodejs \
    npm \
    blas-devel \
    lapack-devel \
    && dnf clean all \
    && rm -rf /var/cache/dnf

USER fluxuser

ENV MPIBIND_INSTALL_PREFIX=/home/fluxuser/mpibind-install \
    GIT_CLONE_STAGING_DIR=/tmp/build \
    PATH=/home/fluxuser/.local/bin:${PATH:-}

RUN pip install --upgrade pip \
    && pip install pybind11 \
    jupyterlab \
    jupyterhub==5.3.0 \
    ipywidgets \
    matplotlib \
    ipykernel \
    && jupyter lab build --dev-build=False \
    && mkdir -p /home/fluxuser/.jupyter \
    && echo "c.ServerApp.ip = '0.0.0.0'" >> /home/fluxuser/.jupyter/jupyter_lab_config.py \
    && echo "c.ServerApp.port = 8888" >> /home/fluxuser/.jupyter/jupyter_lab_config.py \
    && echo "c.ServerApp.open_browser = False" >> /home/fluxuser/.jupyter/jupyter_lab_config.py \
    && echo "c.ServerApp.allow_root = False" >> /home/fluxuser/.jupyter/jupyter_lab_config.py \
    && echo "c.ServerApp.token = ''" >> /home/fluxuser/.jupyter/jupyter_lab_config.py \
    && echo "c.ServerApp.password = ''" >> /home/fluxuser/.jupyter/jupyter_lab_config.py \
    && echo "c.ServerApp.allow_origin = '*'" >> /home/fluxuser/.jupyter/jupyter_lab_config.py \
    && echo "c.ServerApp.base_url = '/'" >> /home/fluxuser/.jupyter/jupyter_lab_config.py \
    && git clone https://github.com/LLNL/mpibind.git ${GIT_CLONE_STAGING_DIR}/mpibind \
	&& cd ${GIT_CLONE_STAGING_DIR}/mpibind \
	&& ./bootstrap \
	&& ./configure --prefix=${MPIBIND_INSTALL_PREFIX} \
	&& make -j install \
    && rm -rf ${GIT_CLONE_STAGING_DIR}

EXPOSE 8888

ENV FLUX_SHELL_RC_PATH=${MPIBIND_INSTALL_PREFIX}/share/mpibind:${FLUX_SHELL_RC_PATH:-}

# Copy and install benchpark
COPY --chown=fluxuser:fluxuser . /home/fluxuser/benchpark

WORKDIR /home/fluxuser/benchpark

RUN pip install -r /home/fluxuser/benchpark/requirements.txt \
    && source /home/fluxuser/benchpark/setup-env.sh \
	&& benchpark bootstrap \
    && pip install .[analyze] \
	&& echo 'source /home/fluxuser/benchpark/setup-env.sh' >> /home/fluxuser/.bashrc

    # && benchpark system init --dest=hpc-tutorial fluxtainer instance_type=${TARGETARCH} \
    # && benchpark experiment init hpc-tutorial kripke +weak caliper=time,mpi scaling-iterations=2 \
    # && benchpark setup hpc-tutorial/kripke/ /home/fluxuser/benchpark/wkp/ \
    # && flux start /home/fluxuser/benchpark/containerfiles/tutorial.sh \
    # && rm -rf /home/fluxuser/benchpark/wkp /home/fluxuser/benchpark/hpc-tutorial *.out \

ENTRYPOINT ["/usr/bin/flux", "start"]
CMD ["/bin/bash"]
