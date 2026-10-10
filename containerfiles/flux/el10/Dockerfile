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

# atlas-devel \ doesn't exist for aarch64

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
    && git clone https://github.com/LLNL/Adiak.git ${GIT_CLONE_STAGING_DIR}/Adiak \
    && cd ${GIT_CLONE_STAGING_DIR}/Adiak \
    && git fetch origin \
    && git checkout v0.5.0 \
    && git submodule update --init --recursive \
    && cmake -B build \
    -DENABLE_MPI=ON \
    -DCMAKE_C_COMPILER=$(which gcc) \
    -DCMAKE_CXX_COMPILER=$(which g++) \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_INSTALL_PREFIX=${CALI_INSTALL_PREFIX} \
    -DENABLE_DOCS=OFF \
    && cmake --build build -j \
    && cmake --install build \
    && git clone https://github.com/LLNL/Caliper.git ${GIT_CLONE_STAGING_DIR}/Caliper \
    && cd ${GIT_CLONE_STAGING_DIR}/Caliper \
    && git fetch origin \
    && git checkout v2.15.0 \
    && git submodule update --init --recursive \
    && cmake -B build \
    -DWITH_TOOLS=ON \
    -DWITH_MPI=ON \
    -DWITH_ADIAK=ON \
    -DWITH_PYTHON_BINDINGS=ON \
    -Dpybind11_DIR=$(pybind11-config --cmakedir) \
    -DCMAKE_PREFIX_PATH=${CALI_INSTALL_PREFIX} \
    -DCMAKE_C_COMPILER=$(which gcc) \
    -DCMAKE_CXX_COMPILER=$(which g++) \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_INSTALL_PREFIX=${CALI_INSTALL_PREFIX} \
    && cmake --build build -j \
    && cmake --install build \
    && pip install llnl-hatchet==2025.2.0 \
    && pip install "llnl-thicket[plotting]==2026.1.0" \
    && git clone https://github.com/LLNL/treescape ${GIT_CLONE_STAGING_DIR}/treescape \
    && cd ${GIT_CLONE_STAGING_DIR}/treescape \
    && git checkout main-2026-04-15 \
    && pip install . \
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
