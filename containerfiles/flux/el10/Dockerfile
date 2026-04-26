FROM fluxrm/flux-core:el10

RUN git clone https://github.com/llnl/benchpark.git && \
	cd benchpark && \
	pip install --upgrade pip && \
	pip install -r requirements.txt && \
	./bin/benchpark list systems

ENTRYPOINT ["/usr/bin/flux", "start", "-s4", "/bin/bash"]
