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
    cam = Cpt(PilatusDetectorCamV33, 'cam1:')
    #stats1 = Cpt(StatsPluginV33, 'Stats1:')
    #stats2 = Cpt(StatsPluginV33, 'Stats2:')
    #stats3 = Cpt(StatsPluginV33, 'Stats3:')
    #stats4 = Cpt(StatsPluginV33, 'Stats4:')
    #stats5 = Cpt(StatsPluginV33, 'Stats5:')
    #roi1 = Cpt(ROIPlugin, 'ROI1:')
    #roi2 = Cpt(ROIPlugin, 'ROI2:')
    #roi3 = Cpt(ROIPlugin, 'ROI3:')
    #roi4 = Cpt(ROIPlugin, 'ROI4:')
    #proc1 = Cpt(ProcessPlugin, 'Proc1:')

    tiff = Cpt(TIFFPluginWithFileStore,
               suffix='TIFF1:',
               write_path_template='/nsls2/data/pdf/legacy/raw/pilatus1_data/%Y/%m/%d/',
               root='/nsls2/data/pdf/legacy/raw')


    def set_exposure_time(self, exposure_time, verbosity=3):
        yield from bps.mv(self.cam.acquire_time, exposure_time, self.cam.acquire_period, exposure_time+.1)
        # self.cam.acquire_time.put(exposure_time)
        # self.cam.acquire_period.put(exposure_time+.1)

    def set_num_images(self, num_images):
        yield from bps.mv(self.cam.num_images, num_images)
        # self.cam.num_images = num_images

# pilatus1 = PilatusV33('XF:28ID1-ES{Det:Pilatus}', name='pilatus1_data')
# pilatus1.tiff.read_attrs = []
# pilatus1.tiff.kind = 'normal'

#for looking at pilatus data

def show_me2(my_im, count_low=0, count_high=1, use_colorbar=False, use_cmap='viridis'):
    #my_low = np.percentile(my_im, per_low)
    #my_high = np.percentile(my_im, per_high)
    plt.imshow(my_im, vmin=count_low, vmax=count_high, cmap= use_cmap)
    if use_colorbar:
        plt.colorbar()



def show_me_db2(
    my_id,
    count_low=1,
    count_high=99,
    use_colorbar=False,
    dark_subtract=False,
    return_im=False,
    return_dark=False,
    new_db = True,
    use_cmap='viridis',
    suffix="_image",
):
    my_det_probably = db[my_id].start["detectors"][0] + suffix
    if new_db:
        my_im = (db[my_id].table(fill=True)[my_det_probably][1][0]).astype(float)
    else:
        my_im = (db[my_id].table(fill=True)[my_det_probably][1]).astype(float)

    if len(my_im) == 0:
        print("issue... passing")
        pass
    if dark_subtract:
        if "sc_dk_field_uid" in db[my_id].start.keys():
            my_dark_id = db[my_id].start["sc_dk_field_uid"]
            if new_db:
                dark_im = (db[my_dark_id].table(fill=True)[my_det_probably][1][0]).astype(float)
            else:
                dark_im = (db[my_dark_id].table(fill=True)[my_det_probably][1]).astype(float)

            my_im = my_im - dark_im
        else:
            print("this run has no associated dark")
    if return_im:
        return my_im
    if return_dark:
        return dark_im

    #if all else fails, plot!
    show_me2(my_im, count_low=count_low, count_high=count_high, use_colorbar=use_colorbar, use_cmap=use_cmap)
