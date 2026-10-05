#!/bin/bash

pip install --upgrade pip \
&& pip install -r requirements.txt \
&& pip install -r docs/requirements.txt \
&& pip install docstrfmt codespell black \
&& source /workspaces/benchpark/setup-env.sh \
&& benchpark bootstrap \
&& cp ~/.bashrc ~/.bashrc.bak \
&& sed -i '$ d' ~/.bashrc
&& echo -e 'source /workspaces/benchpark/setup-env.sh\n' >> ~/.bashrc
