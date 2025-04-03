#!/bin/bash
for url in $(curl -s https://github.com/spack/spack/tree/develop/var/spack/repos/builtin/packages/mfem | grep -o 'href="[^"]*\.patch"' | cut -d'"' -f2); do
    raw_url="https://raw.githubusercontent.com${url/tree/develop/raw/develop}"
    curl -O "$raw_url"
done
