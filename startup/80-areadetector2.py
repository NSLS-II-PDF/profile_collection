import time as ttime
from ophyd.areadetector import (PerkinElmerDetector, ImagePlugin,
                                TIFFPlugin, HDF5Plugin,
                                ProcessPlugin, ROIPlugin)
from ophyd.device import BlueskyInterface
from ophyd.areadetector.trigger_mixins import SingleTrigger, MultiTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreTIFFSquashing,
                                                 FileStoreTIFF)
from ophyd import Signal, EpicsSignal, EpicsSignalRO # Tim test
from ophyd import Component as C, Device, DeviceStatus
from ophyd import StatusBase

from nslsii.ad33 import StatsPluginV33

# from shutter import sh1

#shctl1 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}cam1:ShutterMode', name='shctl1')
#shctl1 = EpicsMotor('XF:28IDC-ES:1{Sh2:Exp-Ax:5}Mtr', name='shctl1')

# monkey patch for trailing slash problem
def _ensure_trailing_slash(path, path_semantics=None):
    """
    'a/b/c' -> 'a/b/c/'
    EPICS adds the trailing slash itself if we do not, so in order for the
    setpoint filepath to match the readback filepath, we need to add the
    trailing slash ourselves.
    """
    newpath = os.path.join(path, '')
    if newpath[0] != '/' and newpath[-1] == '/':
        # make it a windows slash
        newpath = newpath[:-1]
    return newpath

ophyd.areadetector.filestore_mixins._ensure_trailing_slash = _ensure_trailing_slash


class PDFShutter(Device):
    cmd = C(EpicsSignal, 'Cmd-Cmd')
    close_sts = C(EpicsSignalRO, 'Sw:Cls1-Sts')
    open_sts = C(EpicsSignalRO, 'Sw:Opn1-Sts')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._st = None
        self._target = None
        self.close_sts.subscribe(self._watcher_close,
                                 self.close_sts.SUB_VALUE)

        self.open_sts.subscribe(self._watcher_open,
                                self.open_sts.SUB_VALUE)

    def set(self, value, *, wait=False, **kwargs):
        if value not in ('Open', 'Close'):
            raise ValueError(
                "must be 'Open' or 'Close', not {!r}".format(value))
        if wait:
            raise RuntimeError()
        if self._st is not None:
            raise RuntimeError()
        self._target = value
        self._st = st = DeviceStatus(self, timeout=None)
        self.cmd.put(value)

        return st

    def _watcher_open(self, *, old_value=None, value=None, **kwargs):
        print("in open watcher", old_value, value)
        if self._target != 'Open':
            return
        if self._st is None:
            return

        if new_value:
            self._st._finished()
            self._target = None
            self._st = None
        print("in open watcher")

    def _watcher_close(self, *, old_value=None, value=None, **kwargs):
        print("in close watcher", old_value, value)
        if self._target != 'Close':
            return

        if self._st is None:
            return

        if new_value:
            self._st._finished()
            self._target = None
            self._st = None

        pass


class SavedImageSignal(Signal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stashed_datakey = {}

    def describe(self):
        ret = super().describe()
        ret[self.name].update(self.stashed_datakey)
        return ret


def take_dark(cam, light_field, dark_field_name):
    # close shutter

    # take the dark frame
    cam.stage()
    st = cam.trigger()
    while not st.done:
        ttime.sleep(.1)
    ret = cam.read()
    desc = cam.describe()
    cam.unstage()

    # save the df uid
    df = ret[light_field]
    df_sig = getattr(cam, dark_field_name)
    df_sig.put(**df)
    # save the darkfrom description
    df_sig.stashed_datakey = desc[light_field]


class XPDFileStoreTIFFSquashing(FileStoreTIFFSquashing):
    def describe(self):
        description = super().describe()
        key = f"{self.parent.name}_image"
        if not description:
            description[key] = self.parent.make_data_key()
        shape = list(description[key]["shape"])
        shape[0] = self.get_frames_per_point()
        shape = tuple(shape)
        description[key]["shape"] = shape
        description[key].setdefault('dtype_str', '<u2')
        return description


class XPDTIFFPlugin(TIFFPlugin, XPDFileStoreTIFFSquashing,
                    FileStoreIterativeWrite):
    pass


class XPDHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
    pass


class XPDPerkinElmer(PerkinElmerDetector):
    image = C(ImagePlugin, 'image1:')
    _default_configuration_attrs = (
        PerkinElmerDetector._default_configuration_attrs +
        ('images_per_set', 'number_of_sets'))

    tiff = C(XPDTIFFPlugin, 'TIFF1:', #- MA
             #write_path_template='Z:/data/pe1_data/%Y/%m/%d', #- DO
             write_path_template='J:\\%Y\\%m\\%d\\', #- DO
             #write_path_template='Z:/img/%Y/%m/%d/', #- MA
             #read_path_template='/SHARE/img/%Y/%m/%d/', #- MA
             read_path_template='/nsls2/data/pdf/legacy/raw/pe1_data/%Y/%m/%d/', #- DO
             root='/nsls2/data/pdf/legacy/raw/pe1_data/', #-DO
             #root='/SHARE/img/', #-MA
             cam_name='cam',  # used to configure "tiff squashing" #-MA
             proc_name='proc',  # ditto #-MA
             read_attrs=[]) #- MA  
    # hdf5 = C(XPDHDF5Plugin, 'HDF1:',
    #          write_path_template='G:/pe1_data/%Y/%m/%d/',
    #          read_path_template='/direct/XF28ID2/pe1_data/%Y/%m/%d/',
    #          root='/direct/XF28ID2/', reg=db.reg)

    proc = C(ProcessPlugin, 'Proc1:')

    # These attributes together replace `num_images`. They control
    # summing images before they are stored by the detector (a.k.a. "tiff
    # squashing").
    detector_type = C(Signal, value='Perkin', kind='config')
    images_per_set = C(Signal, value=1, add_prefix=())
    number_of_sets = C(Signal, value=1, add_prefix=())

    stats1 = C(StatsPluginV33, 'Stats1:')
    stats2 = C(StatsPluginV33, 'Stats2:')
    stats3 = C(StatsPluginV33, 'Stats3:')
    stats4 = C(StatsPluginV33, 'Stats4:')
    stats5 = C(StatsPluginV33, 'Stats5:')

    roi1 = C(ROIPlugin, 'ROI1:')
    roi2 = C(ROIPlugin, 'ROI2:')
    roi3 = C(ROIPlugin, 'ROI3:')
    roi4 = C(ROIPlugin, 'ROI4:')

    # dark_image = C(SavedImageSignal, None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([(self.cam.trigger_mode, 'Internal'),
                               ])

class XPDPerkinElmer1(XPDPerkinElmer):
    tiff = C(XPDTIFFPlugin, 'TIFF1:', #- MA
             #write_path_template='Z:/data/pe1_data/%Y/%m/%d', #- DO
             write_path_template='J:\\%Y\\%m\\%d\\', #- DO
             #write_path_template='Z:/img/%Y/%m/%d/', #- MA
             #read_path_template='/SHARE/img/%Y/%m/%d/', #- MA
             read_path_template='/nsls2/data/pdf/legacy/raw/pe1_data/%Y/%m/%d/', #- DO
             root='/nsls2/data/pdf/legacy/raw/pe1_data/', #-DO
             #root='/SHARE/img/', #-MA
             cam_name='cam',  # used to configure "tiff squashing" #-MA
             proc_name='proc',  # ditto #-MA
             read_attrs=[], #- MA
    #tiff = C(XPDTIFFPlugin, 'TIFF1:',
             #write_path_template='/home/xf28id1/Documents/Milinda/PE1Data',
             #read_path_template='/SHARE/img/%Y/%m/%d/',
             #root='/SHARE/img/',
             #cam_name='cam',  # used to configure "tiff squashing"
             #proc_name='proc',  # ditto
             #read_attrs=[],

             # TODO: switch to this configuration using GPFS later
             # once G:\ drive is mounted to the Windows IOC
             # (a new Windows 10 machine in the rack upstairs)
             # write_path_template='G:\\img\\%Y\\%m\\%d\\',
             # read_path_template='/nsls2/xf28id1/data/pe1_data/%Y/%m/%d/',
             # root='/nsls2/xf28id1/data/pe1_data',
             )

class XPDPerkinElmer2(XPDPerkinElmer):
    tiff = C(XPDTIFFPlugin, 'TIFF1:', #- MA
             #write_path_template='Z:/data/pe2_data/%Y/%m/%d', #- DO
             write_path_template='Y:\\legacy\\raw\\pe2_data\\%Y\\%m\\%d\\', #- DO
             #write_path_template='Z:/img/%Y/%m/%d/', #- MA
             #read_path_template='/SHARE/img/%Y/%m/%d/', #- MA
             read_path_template='/nsls2/data/pdf/legacy/raw/pe2_data/%Y/%m/%d/', #- DO
             root='/nsls2/data/pdf/legacy/raw/pe2_data/', #-DO
             #root='/SHARE/img/', #-MA
             cam_name='cam',  # used to configure "tiff squashing" #-MA
             proc_name='proc',  # ditto #-MA
             read_attrs=[], #- MA
    #tiff = C(XPDTIFFPlugin, 'TIFF1:',
             #write_path_template='/home/xf28id1/Documents/Milinda/PE1Data',
             #read_path_template='/SHARE/img/%Y/%m/%d/',
             #root='/SHARE/img/',
             #cam_name='cam',  # used to configure "tiff squashing"
             #proc_name='proc',  # ditto
             #read_attrs=[],

             # TODO: switch to this configuration using GPFS later
             # once G:\ drive is mounted to the Windows IOC
             # (a new Windows 10 machine in the rack upstairs)
             # write_path_template='G:\\img\\%Y\\%m\\%d\\',
             # read_path_template='/nsls2/xf28id1/data/pe2_data/%Y/%m/%d/',
             # root='/nsls2/xf28id1/data/pe1_data',
             )


class ContinuousAcquisitionTrigger(BlueskyInterface):
    """
    This trigger mixin class records images when it is triggered.

    It expects the detector to *already* be acquiring, continously.
    """
    def __init__(self, *args, plugin_name=None, image_name=None, **kwargs):
        if plugin_name is None:
            raise ValueError("plugin name is a required keyword argument")
        super().__init__(*args, **kwargs)
        self._plugin = getattr(self, plugin_name)
        if image_name is None:
            image_name = '_'.join([self.name, 'image'])
        self._plugin.stage_sigs[self._plugin.auto_save] = 'No'
        self.cam.stage_sigs[self.cam.image_mode] = 'Continuous'
        self._plugin.stage_sigs[self._plugin.file_write_mode] = 'Capture'
        self._image_name = image_name
        self._status = None
        self._num_captured_signal = self._plugin.num_captured
        self._num_captured_signal.subscribe(self._num_captured_changed)
        self._save_started = False

    def stage(self):
        if self.cam.acquire.get() != 1:
             ##foolishly added by DO
             try:
                self.cam.acquire.put(1)
                print ("The detector wasn't properly acquiring :(")
                time.sleep(1)
                print ("Don't worry, I probably fixed it for you!")
             except:
                 raise RuntimeError("The ContinuousAcuqisitionTrigger expects "
                                    "the detector to already be acquiring."
                                    "I was unable to fix it, please restart the ui.") #new line, DO
             #old style, simple runtime error (no rescue attempt)
             #raise RuntimeError("The ContinuousAcuqisitionTrigger expects "
             #                   "the detector to already be acquiring.")
             
        #if we get this far, we can now stage the detector. 
        super().stage()
        
        # put logic to look up proper dark frame
        # die if none is found

    def trigger(self):
        "Trigger one acquisition."
        if not self._staged:
            raise RuntimeError("This detector is not ready to trigger."
                               "Call the stage() method before triggering.")
        self._save_started = False
        self._status = DeviceStatus(self)
        self._desired_number_of_sets = self.number_of_sets.get()
        self._plugin.num_capture.put(self._desired_number_of_sets)
        self.dispatch(self._image_name, ttime.time())
        #self.generate_datum(self._image_name, ttime.time())
        # reset the proc buffer, this needs to be generalized
        self.proc.reset_filter.put(1)
        self._plugin.capture.put(1)  # Now the TIFF plugin is capturing.
        return self._status

    def _num_captured_changed(self, value=None, old_value=None, **kwargs):
        "This is called when the 'acquire' signal changes."
        if self._status is None:
            return
        if value == self._desired_number_of_sets:
            # This is run on a thread, so exceptions might pass silently.
            # Print and reraise so they are at least noticed.
            try:
                self.tiff.write_file.put(1)
            except Exception as e:
                print(e)
                raise
            self._save_started = True
        if value == 0 and self._save_started:
            self._status._finished()
            self._status = None
            self._save_started = False



class PerkinElmerContinuous1(ContinuousAcquisitionTrigger, XPDPerkinElmer1):
    pass


class PerkinElmerStandard1(SingleTrigger, XPDPerkinElmer1):
    pass


class PerkinElmerMulti1(MultiTrigger, XPDPerkinElmer1):
    shutter = C(EpicsSignal, 'XF:28IDC-ES:1{Sh:Exp}Cmd-Cmd')

class PerkinElmerContinuous2(ContinuousAcquisitionTrigger, XPDPerkinElmer2):
    pass


class PerkinElmerStandard2(SingleTrigger, XPDPerkinElmer2):
    pass


class PerkinElmerMulti2(MultiTrigger, XPDPerkinElmer2):
    shutter = C(EpicsSignal, 'XF:28IDC-ES:1{Sh:Exp}Cmd-Cmd')

#temporary disable detector for testing -DO 11/25/19
pe1 = PerkinElmerStandard1('XF:28ID1-ES{Det:PE1}', name='pe1', read_attrs=['tiff'])
#################


#pe1.stage_sigs.pop('cam.acquire')

################
#Enabled for PE2 detector testing 11/25/19 - disabled for startup 8/22/2023 DO
pe2 = PerkinElmerStandard2('XF:28ID1-ES{Det:PE2}', name='pe2', read_attrs=['tiff'])
#################


#temporary disable detector for PE2 testing -MA 11/25/19 and 12/09/21
pe1c = PerkinElmerContinuous1('XF:28ID1-ES{Det:PE1}', name='pe1c',
                            read_attrs=['tiff', 'stats1.total'],
                             plugin_name='tiff')
################ - disabled for startup 8/22/2023 DO
pe2c = PerkinElmerContinuous2('XF:28ID1-ES{Det:PE2}', name='pe2c',
                            read_attrs=['tiff', 'stats1.total'],
                             plugin_name='tiff')

################
#enabled by MA during PE2 SAXS - 01/2022 and 12/09/22
#pe1c = PerkinElmerContinuous2('XF:28ID1-ES{Det:PE2}', name='pe1c',
#                             read_attrs=['tiff', 'stats1.total'],
#                             plugin_name='tiff')
#################

#temporary disable detector for testing -DO 7/11/19
pe1c.detector_type.kind='config'
pe1.detector_type.kind='config'
################### - disabled for startup 8/22/2023 DO
pe2c.detector_type.kind='config'
pe2.detector_type.kind='config'

import time
class CachedDetector:
    '''
        This is a dark image detector. It doesn't do anything.
        This detector does not support a hierarchy of devices!

    '''
    def __init__(self, det, attrs, expire_time):
        '''
            Initialize the detector det.
            det : the detector
            attrs : the attrs to read from
            expire_time : the expiration time
        '''
        self._det = det
        self._attrs = attrs
        self._expire_time = expire_time
        self._read_cache = dict()
        self._current_read = None

    def trigger(self):
        '''
            Trigger the detector.
            Checks the cache and time
        '''
        # check the cache
        attr_vals = (obj.get() for obj in self._attrs)
        self._cur_attr_vals = attr_vals

        read_val = self._read_cache.get(attr_vals, None)
        if read_val is None:
            self._det.trigger()
            new_val = self._det.read()
            self._read_cache[attr_vals] = {'time': time.time(),
                                            'data':  new_val}
        # trigger etc need to finish later
        data = self._read_cache[attr_vals]
        if np.abs(data['time']-time.time()) . self._expire_time:
            self._det.trigger()
            new_val = self._det.read()
            self._read_cache[attr_vals] = {'time': time.time(),
                                            'data':  new_val}


    def read(self):
        return self._read_cache[self_cur_attr_vals]['data']


    # TODO: maybe check if det is staged
    def stage(self):
        pass

    def unstage(self):
        pass

# some defaults, as an example of how to use this
# pe1.configure(dict(images_per_set=6, number_of_sets=10))

