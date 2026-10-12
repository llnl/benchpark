FROM fluxrm/flux-core:el10

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
    && dnf clean all \
    && rm -rf /var/cache/dnf

USER fluxuser

ENV CALI_INSTALL_PREFIX=/home/fluxuser/caliper-install \
    MPIBIND_INSTALL_PREFIX=/home/fluxuser/mpibind-install \
    GIT_CLONE_STAGING_DIR=/tmp/build \
    PATH=/home/fluxuser/.local/bin:${PATH:-}

RUN pip install --upgrade pip \
    && pip install pybind11 \
    && source /etc/profile.d/modules.sh \
    && module load mpi \
    && git clone https://github.com/LLNL/mpibind.git ${GIT_CLONE_STAGING_DIR}/mpibind \
	&& cd ${GIT_CLONE_STAGING_DIR}/mpibind \
	&& ./bootstrap \
	&& ./configure --prefix=${MPIBIND_INSTALL_PREFIX} \
	&& make -j install \
    && rm -rf ${GIT_CLONE_STAGING_DIR}

ENV FLUX_SHELL_RC_PATH=${MPIBIND_INSTALL_PREFIX}/share/mpibind:${FLUX_SHELL_RC_PATH:-} \
    PATH=${CALI_INSTALL_PREFIX}/bin:${PATH:-} \
    LD_LIBRARY_PATH=${CALI_INSTALL_PREFIX}/lib:${CALI_INSTALL_PREFIX}/lib64:${LD_LIBRARY_PATH:-} \
    PYTHONPATH=${CALI_INSTALL_PREFIX}/lib/python3.9/site-packages:${PYTHONPATH:-}

# Copy and install benchpark
COPY --chown=fluxuser:fluxuser . /home/fluxuser/benchpark

WORKDIR /home/fluxuser/benchpark

RUN pip install -r requirements.txt \
	&& ./bin/benchpark bootstrap \
	&& echo 'source /home/fluxuser/benchpark/setup-env.sh' >> /home/fluxuser/.bashrc

ENTRYPOINT ["/usr/bin/flux", "start"]
CMD ["/bin/bash"]
