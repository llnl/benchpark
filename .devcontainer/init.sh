#!/bin/bash

pip install -r requirements.txt \
&& pip install -r requirements/docs.txt \
&& pip install -r requirements/style.txt \
&& source /workspaces/benchpark/setup-env.sh \
&& benchpark bootstrap \
&& pip install .[analyze] \
&& sed -i 's|home/fluxuser|workspaces|g' ~/.bashrc \
&& /usr/bin/flux start
