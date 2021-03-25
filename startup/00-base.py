# Make ophyd listen to pyepics.
import logging
import matplotlib.pyplot
import nslsii
import time
import matplotlib.pyplot as plt

from bluesky.utils import ts_msg_hook

# See docstring for nslsii.configure_base() for more details
# this command takes away much of the boilerplate for settting up a profile
# (such as setting up best effort callbacks etc)
nslsii.configure_base(
    get_ipython().user_ns,
    'pdf',
    pbar=True,
    bec=True,
    magics=True,
    mpl=False,
    publish_documents_to_kafka=True
)

from pathlib import Path

import appdirs


try:
    from bluesky.utils import PersistentDict
except ImportError:
    import msgpack
    import msgpack_numpy
    import zict

    class PersistentDict(zict.Func):
        def __init__(self, directory):
            self._directory = directory
            self._file = zict.File(directory)
            super().__init__(self._dump, self._load, self._file)

        @property
        def directory(self):
            return self._directory

        def __repr__(self):
            return f"<{self.__class__.__name__} {dict(self)!r}>"

        @staticmethod
        def _dump(obj):
            "Encode as msgpack using numpy-aware encoder."
            # See https://github.com/msgpack/msgpack-python#string-and-binary-type
            # for more on use_bin_type.
            return msgpack.packb(
                obj,
                default=msgpack_numpy.encode,
                use_bin_type=True)

        @staticmethod
        def _load(file):
            return msgpack.unpackb(
                file,
                object_hook=msgpack_numpy.decode,
                raw=False)

runengine_metadata_dir = appdirs.user_data_dir(appname="bluesky") / Path("runengine-metadata")

# PersistentDict will create the directory if it does not exist
RE.md = PersistentDict(runengine_metadata_dir)

# disable plotting for now
# bec.disable_plots()
# Optional: set any metadata that rarely changes.
# RE.md['beamline_id'] = 'YOUR_BEAMLINE_HERE'

# At the end of every run, verify that files were saved and
# print a confirmation message.
#from bluesky.callbacks.broker import verify_files_saved, post_run
# RE.subscribe(post_run(verify_files_saved, db), 'stop')

# RE.msg_hook = ts_msg_hook

########## New logging 8/24/2020

import logging
#logging.getLogger('ophyd').handlers[0].setLevel('WARNING')
logger = logging.getLogger('ophyd')
logger.setLevel('WARNING')

###########

RE.md['facility'] = 'NSLS-II'
RE.md['group'] = 'PDF'
RE.md['beamline_id'] = '28-ID-1'
RE.md['cycle'] = '2018-1'

def get_user_info():
    ''' This function prompts the user for basic info and
        adds it to RE.md.

        All data in RE.md gets saved in each start document for each run.

    '''

    print("Please enter the following information for your scan")

    PI_name = input("Enter PI Name: ")
    prop_ID = input("Enter Proposal ID: ")
    wavelength = input("Enter wavelength: ")

    RE.md['PI Name'] = PI_name
    RE.md['Proposal ID'] = prop_ID
    RE.md['wavelength'] = wavelength

# get_user_info()

from bluesky.magics import BlueskyMagics
from ophyd import EpicsSignal, EpicsSignalRO


def which_pvs(cls=None):
    ''' returns list of all existing pv's.
        cls : class, optional
            the class of PV's to search for
            defaults to [Device, Signal]
    '''
    if cls is None:
        cls = [Device, Signal]
    user_ns = get_ipython().user_ns

    obj_list = list()
    for key, obj in user_ns.items():
        # ignore objects beginning with "_"
        # (mainly for ipython stored objs from command line
        # return of commands)
        # also check its a subclass of desired classes
        if not key.startswith("_") and isinstance(obj, tuple(cls)):
            obj_list.append((key, obj))

    return obj_list


def print_all_pvs():
    cols = ["Python name", "Ophyd Name"]
    print("{:20s} \t {:20s}".format(*cols))
    print("="*40)
    obj_list = which_pvs()
    for name, obj in obj_list:
        print("{:20s} \t {:20s}".format(name, obj.name))
        try:
            if not isinstance(obj, EpicsMotor):
                for comp in obj.component_names:
                    print("    {}".format(comp))
        except AttributeError:
            pass


def print_all_pv_values():
    cols = ["Python name", "Time stamp", "Value"]
    print("{:40s} \t {:20s} \t\t\t {:20s}".format(*cols))
    print("="*120)
    obj_list = which_pvs()
    for name, obj in obj_list:
        try:
            ret = obj.read()
        except AttributeError:
            pass

        for key, val in ret.items():
            print("{:40s} \t {:20s} \t {}".format(key, time.ctime(val['timestamp']), val['value']))
