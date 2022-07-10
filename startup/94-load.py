#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
import yaml

from xpdacq.xpdacq_conf import (
    _load_beamline_config,
    _reload_glbl,
    _set_glbl,
    configure_device,
    glbl_dict,
)

# configure experiment device being used in current version
if glbl_dict["is_simulation"]:
    from xpdacq.simulation import xpd_pe1c, db, cs700, shctl1, ring_current, fb

    pe1c = xpd_pe1c  # alias

configure_device(
    area_det=pe1c,
    shutter=fs,
    temp_controller=eurotherm,  # changed from None to eurotherm on 3/22/19 - DPO
    db=db,
    filter_bank=fb,
    ring_current=ring_current,
)

# cache previous glbl state
reload_glbl_dict = _reload_glbl()
from xpdacq.glbl import glbl

# reload beamtime
from xpdacq.beamtimeSetup import start_xpdacq, _start_beamtime, _end_beamtime

bt = start_xpdacq()
if bt is not None:
    print("INFO: Reload beamtime objects:\n{}\n".format(bt))
if reload_glbl_dict is not None:
    _set_glbl(glbl, reload_glbl_dict)

# import necessary modules
from xpdacq.xpdacq import *
from xpdacq.beamtime import *
from xpdacq.utils import import_sample_info

# instantiate xrun without beamtime, like bluesky setup
xrun = CustomizedRunEngine(None)
xrun.md["beamline_id"] = glbl["beamline_id"]
xrun.md["group"] = glbl["group"]
xrun.md["facility"] = glbl["facility"]
with open(glbl["blconfig_path"], "r") as f:
    beamline_config = yaml.unsafe_load(f)
xrun.md["beamline_config"] = beamline_config

# insert header to db, either simulated or real
xrun.subscribe(db.insert, "all")

# We need to repeat it here for `xrun` as RE is not used here...
nslsii.configure_kafka_publisher(xrun, "pdf")

if bt:
    xrun.beamtime = bt

HOME_DIR = glbl["home"]
BASE_DIR = glbl["base"]

print("INFO: Initializing the XPD data acquisition environment\n")
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

# See https://github.com/silx-kit/pyFAI/issues/1399#issuecomment-694185304
import logging

logging.getLogger().addHandler(logging.NullHandler())

from xpdacq.calib import *

# analysis functions, only at beamline
# from xpdan.data_reduction import *

print("OK, ready to go.  To continue, follow the steps in the xpdAcq")
print("documentation at http://xpdacq.github.io/xpdacq\n")


class MoreCustomizedRunEngine(CustomizedRunEngine):
    def __call__(self, plan, *args, **kwargs):
        super().__call__({}, plan, *args, **kwargs)


from bluesky.utils import ts_msg_hook
RE = MoreCustomizedRunEngine(None)
RE.msg_hook = ts_msg_hook
RE.md.update(xrun.md)
# insert header to db, either simulated or real
RE.subscribe(db.insert, "all")
RE.beamtime = bt
RE.clear_suspenders()

del Tramp
del Tlist
