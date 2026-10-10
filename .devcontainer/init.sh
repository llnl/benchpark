#!/bin/bash

pip install -r requirements.txt \
&& pip install -r docs/requirements.txt \
&& pip install docstrfmt codespell black \
&& source /workspaces/benchpark/setup-env.sh \
&& benchpark bootstrap \
&& sed -i 's|home/fluxuser|workspaces|g' ~/.bashrc \
&& /usr/bin/flux start
