FROM fluxrm/flux-core:el10

USER root

RUN dnf clean all \
	&& rm -rf /var/cache/dnf \
	&& git config --global checkout.workers 1024 \
	&& git config --global feature.manyFiles true \
    && git config --global core.sharedRepository false \
	&& echo "* soft memlock unlimited" >> /etc/security/limits.conf \
    && echo "* hard memlock unlimited" >> /etc/security/limits.conf

# Install additional dependencies for Caliper/Adiak and analysis tools
RUN dnf install -y \
    cmake \
    gcc-c++ \
    python3-devel \
    wget \
    gzip \
    patch \
    tar \
    unzip \
    xz \
    zstd \
    bzip2 \
    atlas-devel \
    gettext \
    ncurses-devel \
    sqlite \
    && dnf clean all \
    && rm -rf /var/cache/dnf

USER fluxuser

# Install mpibind
RUN git clone https://github.com/LLNL/mpibind.git \
	&& mkdir build \
	&& cd mpibind \
	&& ./bootstrap \
	&& ./configure --prefix=$(pwd)/../build \
	&& make -j install

ENV FLUX_SHELL_RC_PATH=/home/fluxuser/build/share/mpibind:$FLUX_SHELL_RC_PATH

# Install Adiak and Caliper
ENV CALI_INSTALL_PREFIX=/home/fluxuser/caliper-install \
    GIT_CLONE_STAGING_DIR=/tmp/build

USER root

RUN git clone https://github.com/LLNL/Caliper.git ${GIT_CLONE_STAGING_DIR}/Caliper && \
    cd ${GIT_CLONE_STAGING_DIR}/Caliper && \
    git fetch origin && \
    git checkout v2.15.0 && \
    git submodule update --init --recursive && \
    git clone https://github.com/LLNL/Adiak.git ${GIT_CLONE_STAGING_DIR}/Adiak && \
    cd ${GIT_CLONE_STAGING_DIR}/Adiak && \
    git fetch origin && \
    git checkout v0.5.0 && \
    git submodule update --init --recursive

RUN cd ${GIT_CLONE_STAGING_DIR}/Adiak && \
    mkdir build && \
    cd build && \
    cmake \
    -DENABLE_MPI=ON \
    -DCMAKE_C_COMPILER=$(which gcc) \
    -DCMAKE_CXX_COMPILER=$(which g++) \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_INSTALL_PREFIX=${CALI_INSTALL_PREFIX} \
    .. && \
    make -j 4 && \
    make install

RUN pip install pybind11

RUN cd ${GIT_CLONE_STAGING_DIR}/Caliper && \
    mkdir build && \
    cd build && \
    cmake \
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
    .. && \
    make -j 4 && \
    make install

RUN rm -rf ${GIT_CLONE_STAGING_DIR}/Caliper && rm -rf ${GIT_CLONE_STAGING_DIR}/Adiak

# Update environment for Caliper
ENV PATH=${CALI_INSTALL_PREFIX}/bin:$PATH \
    LD_LIBRARY_PATH=${CALI_INSTALL_PREFIX}/lib:${CALI_INSTALL_PREFIX}/lib64:$LD_LIBRARY_PATH \
    PYTHONPATH=${CALI_INSTALL_PREFIX}/lib/python3.9/site-packages:$PYTHONPATH

# Install analysis tools: hatchet, thicket, treescape
RUN pip install llnl-hatchet==2025.2.0 && \
    pip install "llnl-thicket[plotting]==2026.1.0"

RUN git clone https://github.com/LLNL/treescape ${GIT_CLONE_STAGING_DIR}/treescape && \
    cd ${GIT_CLONE_STAGING_DIR}/treescape && \
    git checkout main-2026-04-15 && \
    pip install .

RUN rm -rf ${GIT_CLONE_STAGING_DIR}/treescape

USER fluxuser

# Copy and install benchpark
COPY --chown=fluxuser:fluxuser . /home/fluxuser/benchpark

WORKDIR /home/fluxuser/benchpark

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
	&& ./bin/benchpark bootstrap \
	&& echo 'source /home/fluxuser/benchpark/setup-env.sh' >> /home/fluxuser/.bashrc

ENTRYPOINT ["/home/fluxuser/benchpark/containerfiles/entrypoint.sh"]
