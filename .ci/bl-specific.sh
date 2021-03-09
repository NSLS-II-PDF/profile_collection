#!/bin/bash

# cp -v <...> ~/.ipython/profile_${TEST_PROFILE}/

conda install -y -c ${CONDA_CHANNEL_NAME} xpdacq

mkdir -v -p ~/.config/acq/
cp -v .ci/pdf.yml ~/.config/acq/
cp -v .ci/glbl.yml ~/.config/acq/
