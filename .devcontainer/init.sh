#!/bin/bash

pip install -r requirements.txt \
&& pip install -r docs/requirements.txt \
&& pip install -r .github/workflows/requirements/style.txt \
&& pip install -r .github/workflows/requirements/docs.txt \
&& source /workspaces/benchpark/setup-env.sh \
&& benchpark bootstrap \
&& pip install .[analyze] \
&& sed -i 's|home/fluxuser|workspaces|g' ~/.bashrc \
&& /usr/bin/flux start
