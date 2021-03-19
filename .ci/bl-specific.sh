#!/bin/bash

# cp -v <...> ~/.ipython/profile_${TEST_PROFILE}/

# xpdacq is already installed in the 'collection-2021-1.2' conda env.
if [ "$CONDA_ENV_NAME" == "collection-2021-1.0" ]; then
    conda install -y -c ${CONDA_CHANNEL_NAME} xpdacq
fi

mkdir -v -p ~/.config/acq/
mkdir -v -p ~/user_data/config_base/yml/
sudo mkdir -v -p /mnt/data/bnl/xpdacq_special/data/xpdConfig/
sudo chown -Rv $USER: /mnt/data/bnl/xpdacq_special/data/xpdConfig/

cp -v .ci/pdf.yml ~/.config/acq/
cp -v .ci/glbl.yml ~/user_data/config_base/yml/
cp -v .ci/xpd_beamline_config.yml /mnt/data/bnl/xpdacq_special/data/xpdConfig/

