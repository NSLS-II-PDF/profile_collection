"""XpdAcq Initializatoion
>>>>>>> MNT: use new 94-load.py

Initialize the XpdAcq objects for xpdacq >= 1.1.0.
This file will do the following changes to the name space:

    (1) create objects of `xrun`, `glbl` etc. using the UserInterface class in XpdAcq.
    (2) import helper functions for users from XpdAcq
    (3) change the home directory to `glbl['home']` or `glbl['base']`
    (4) disable the logging of pyFAI

XpdAcq < 1.1.0 uses the 94-load.bak file.
"""
import os

# Disable interactive logging of pyFAI
# See https://github.com/silx-kit/pyFAI/issues/1399#issuecomment-694185304
os.environ["PYFAI_NO_LOGGING"] = "1"

from xpdacq.utils import import_userScriptsEtc, import_sample_info
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.beamtime import ScanPlan, Sample, ct, Tramp, Tlist, tseries
from xpdacq.ipysetup import UserInterface

# Do all setup in the constructor of UserInterface
# HOME directory will be changed to the one in glbl
ui = UserInterface(
    area_dets=[pe1c],
    det_zs=[None],
    shutter=fs,
    temp_controller=eurotherm,
    filter_bank=fb,
    ring_current=ring_current,
    db=db
)
xrun = ui.xrun
glbl = ui.glbl
xpd_configuration = ui.xpd_configuration
run_calibration = ui.run_calibration
bt = ui.bt

# Remove the variables that won't be used
del UserInterface, ui
