from ophyd import Component as Cpt
from ophyd import Signal

from ophyd import (
    SingleTrigger,
    TIFFPlugin,
    ImagePlugin,
    DetectorBase,
    HDF5Plugin,
    AreaDetector,
    EpicsSignal,
    EpicsSignalRO,
    ROIPlugin,
    TransformPlugin,
    ProcessPlugin,
    PilatusDetector,
    PilatusDetectorCam)
from ophyd.areadetector.plugins import (
    StatsPlugin_V34 as StatsPlugin
)
from nslsii.ad33 import SingleTriggerV33


class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    pass


class PilatusDetectorCamV33(PilatusDetectorCam):
    wait_for_plugins = Cpt(EpicsSignal, "WaitForPlugins", string=True, kind="config")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs["wait_for_plugins"] = "Yes"

    def ensure_nonblocking(self):
        self.stage_sigs["wait_for_plugins"] = "Yes"
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, "ensure_nonblocking"):
                cpt.ensure_nonblocking()


class PilatusV33(SingleTriggerV33, PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    #    stats1 = Cpt(StatsPlugin, 'Stats1:')
    #    stats2 = Cpt(StatsPlugin, 'Stats2:')
    #    stats3 = Cpt(StatsPlugin, 'Stats3:')
    #    stats4 = Cpt(StatsPlugin, 'Stats4:')
    #    stats5 = Cpt(StatsPlugin, 'Stats5:')
    #    roi1 = Cpt(ROIPlugin, 'ROI1:')
    #    roi2 = Cpt(ROIPlugin, 'ROI2:')
    #    roi3 = Cpt(ROIPlugin, 'ROI3:')
    #    roi4 = Cpt(ROIPlugin, 'ROI4:')
    #    proc1 = Cpt(ProcessPlugin, 'Proc1:')

    tiff = Cpt(
        TIFFPluginWithFileStore,
        suffix="TIFF1:",
        write_path_template="/nsls2/data/pdf/legacy/raw/pilatus300/%Y/%m/%d/",
        root="/nsls2/data/pdf/legacy/raw",
    )

    def setExposureTime(self, exposure_time, verbosity=3):
        self.cam.acquire_time.put(exposure_time)
        self.cam.acquire_period.put(exposure_time + 0.1)


pilatus300 = PilatusV33("XF:28ID1-ES{Det:PIL3X}:", name="pilatus300")
pilatus300.tiff.read_attrs = []

# pilatus300.stats3.total.kind = 'hinted'
# pilatus300.stats4.total.kind = 'hinted'
