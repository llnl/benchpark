FROM fluxrm/flux-core:el10

USER root

RUN dnf clean all \
	&& rm -rf /var/cache/dnf \
	&& git config --global checkout.workers 1024 \
	&& git config --global feature.manyFiles true \
	&& echo "* soft memlock unlimited" >> /etc/security/limits.conf \
    && echo "* hard memlock unlimited" >> /etc/security/limits.conf

USER fluxuser

RUN git clone https://github.com/LLNL/mpibind.git \
	&& mkdir build \
	&& cd mpibind \
	&& ./bootstrap \
	&& ./configure --prefix=$(pwd)/../build \
	&& make -j install

ENV FLUX_SHELL_RC_PATH=/home/fluxuser/build/share/mpibind:$FLUX_SHELL_RC_PATH

COPY --chown=fluxuser:fluxuser . /home/fluxuser/benchpark

WORKDIR /home/fluxuser/benchpark

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
	&& ./bin/benchpark bootstrap \
	&& echo 'source /home/fluxuser/benchpark/setup-env.sh' >> /home/fluxuser/.bashrc

ENTRYPOINT ["/home/fluxuser/benchpark/containerfiles/entrypoint.sh"]
