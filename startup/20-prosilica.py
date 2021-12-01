import time as ttime  # tea time
from types import SimpleNamespace
from datetime import datetime
from ophyd import (
    ProsilicaDetector,
    SingleTrigger,
    TIFFPlugin,
    ImagePlugin,
    StatsPlugin,
    DetectorBase,
    HDF5Plugin,
    AreaDetector,
    EpicsSignal,
    EpicsSignalRO,
    ROIPlugin,
    TransformPlugin,
    ProcessPlugin,
    Device,
)
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.areadetector.base import ADComponent, EpicsSignalWithRBV
from ophyd.areadetector.filestore_mixins import (
    FileStoreTIFFIterativeWrite,
    FileStoreHDF5IterativeWrite,
    FileStoreBase,
    new_short_uid,
    FileStoreIterativeWrite,
)
from ophyd import Component as Cpt, Signal
from ophyd.utils import set_and_wait
from pathlib import PurePath
from bluesky.plan_stubs import (
    stage,
    unstage,
    open_run,
    close_run,
    trigger_and_read,
    pause,
)
from collections import OrderedDict


class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    """Add this as a component to detectors that write TIFFs."""

    pass


class TIFFPluginEnsuredOff(TIFFPlugin):
    """Add this as a component to detectors that do not write TIFFs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([("auto_save", "No")])


class StandardProsilica(SingleTrigger, ProsilicaDetector):
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPlugin, "Stats1:")
    stats2 = Cpt(StatsPlugin, "Stats2:")
    stats3 = Cpt(StatsPlugin, "Stats3:")
    stats4 = Cpt(StatsPlugin, "Stats4:")
    stats5 = Cpt(StatsPlugin, "Stats5:")
    trans1 = Cpt(TransformPlugin, "Trans1:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")

    # This class does not save TIFFs. We make it aware of the TIFF plugin
    # only so that it can ensure that the plugin is not auto-saving.
    tiff = Cpt(TIFFPluginEnsuredOff, suffix="TIFF1:")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("labels", ["cameras"])
        super().__init__(*args, **kwargs)
        self.stats1.total.kind = "hinted"


class StandardProsilicaWithTIFF(StandardProsilica):
    tiff = Cpt(
        TIFFPluginWithFileStore,
        suffix="TIFF1:",
        write_path_template="/nsls2/data/pdf/legacy/raw/psccd/%Y/%m/%d/",
        root="/nsls2/data/pdf/legacy/raw/psccd",
    )


## This renaming should be reversed: no correspondance between CSS screens, PV names and ophyd....
# As of May 25, 2018 the cameras are not working
"""
Test_Cam1 = StandardProsilicaWithTIFF('XF:28ID1-BI{Test-Cam:1}', name='Test_Cam1')
Cam2 = StandardProsilicaWithTIFF('XF:28ID1-BI{Cam:2}', name='Cam2')

all_standard_pros = [Test_Cam1, Cam2]

for camera in all_standard_pros:
    camera.read_attrs = ['stats1', 'stats2', 'stats3', 'stats4', 'stats5']
    # camera.tiff.read_attrs = []  # leaving just the 'image'
    for stats_name in ['stats1', 'stats2', 'stats3', 'stats4', 'stats5']:
        stats_plugin = getattr(camera, stats_name)
        stats_plugin.read_attrs = ['total']
        camera.stage_sigs[stats_plugin.blocking_callbacks] = 1

    camera.stage_sigs[camera.roi1.blocking_callbacks] = 1
    camera.stage_sigs[camera.trans1.blocking_callbacks] = 1
    camera.stage_sigs[camera.cam.trigger_mode] = 'Fixed Rate'

for camera in [Test_Cam1, Cam2]:
    camera.read_attrs.append('tiff')
    camera.tiff.read_attrs = []
"""
