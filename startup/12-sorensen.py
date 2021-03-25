from ophyd import EpicsSignal
import numpy as np
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
import time as ttime


# This is fixed in ophyd 1.6.2
def _paranoid_set_and_wait(
    signal, val, poll_time=0.01, timeout=10, rtol=None, atol=None
):
    """Set a signal to a value and wait until it reads correctly.

    For floating point values, it is strongly recommended to set a tolerance.
    If tolerances are unset, the values will be compared exactly.

    Parameters
    ----------
    signal : EpicsSignal (or any object with `get` and `put`)
    val : object
        value to set signal to
    poll_time : float, optional
        how soon to check whether the value has been successfully set
    timeout : float, optional
        maximum time to wait for value to be successfully set
    rtol : float, optional
        allowed relative tolerance between the readback and setpoint values
    atol : float, optional
        allowed absolute tolerance between the readback and setpoint values

    Raises
    ------
    TimeoutError if timeout is exceeded
    """
    from bluesky.utils.epics_pvs import _compare_maybe_enum, logger
    import time as ttime

    signal.put(val)
    expiration_time = ttime.time() + timeout if timeout is not None else None
    current_value = signal.get()

    if atol is None and hasattr(signal, "tolerance"):
        atol = signal.tolerance
    if rtol is None and hasattr(signal, "rtolerance"):
        rtol = signal.rtolerance

    try:
        enum_strings = signal.enum_strs
    except AttributeError:
        enum_strings = ()

    if atol is not None:
        within_str = ["within {!r}".format(atol)]
    else:
        within_str = []

    if rtol is not None:
        within_str.append("(relative tolerance of {!r})".format(rtol))

    if within_str:
        within_str = " ".join([""] + within_str)
    else:
        within_str = ""

    while current_value is None or not _compare_maybe_enum(
        val, current_value, enum_strings, atol, rtol
    ):
        logger.debug(
            "Waiting for %s to be set from %r to %r%s...",
            signal.name,
            current_value,
            val,
            within_str,
        )
        ttime.sleep(poll_time)
        if poll_time < 0.1:
            poll_time *= 2  # logarithmic back-off
        current_value = signal.get()
        if expiration_time is not None and ttime.time() > expiration_time:
            raise TimeoutError(
                "Attempted to set %r to value %r and timed "
                "out after %r seconds. Current value is %r."
                % (signal, val, timeout, current_value)
            )


class ParnoidEpicsSignal(EpicsSignal):
    def _set_and_wait(self, val):
        return _paranoid_set_and_wait(
            self, value, timeout=timeout, atol=self.tolerance, rtol=self.rtolerance
        )

    def get(self):
        ret = super().get()
        for j in range(5):
            if ret is not None:
                return ret
            ttime.sleep(0.1)
            ret = super().get()
        else:
            raise RuntimeError("getting all nones")


sorensen850_manual = ParnoidEpicsSignal(
    "XF:28ID1-ES{LS336:1-Out:3}Out:Man-RB",
    write_pv="XF:28ID1-ES{LS336:1-Out:3}Out:Man-SP",
    name="sorensen850_manual",
    tolerance=0.1,
)
import uuid
import bluesky.plans as bp

lakeshore336.read_attrs = ["temp", "temp.C", "temp.C.T"]
lakeshore336.temp.C.T.kind = "hinted"


def power_ramp(start, stop, steps, *, exposure, settle_time=0, n_per_hold=1, **kwargs):
    ramp_uid = str(uuid.uuid4())
    for p in np.linspace(start, stop, steps):
        yield from bps.mv(sorensen850_manual, p)
        if settle_time > 0:
            yield from bps.sleep(settle_time)
        for j in range(n_per_hold):
            yield from bpp.baseline_wrapper(
                simple_ct(
                    [pe1c] + [sorensen850_manual, lakeshore336],
                    md={"ramp_uid": ramp_uid},
                    **kwargs,
                    exposure=exposure,
                ),
                [lakeshore336, ring_current, sorensen850_manual],
            )


from pathlib import Path
import pandas as pd


def write_single_calibration_data_to_csv_and_make_tom_sad(uid, path=Path(".")):
    h = db[uid]
    tbl = h.table()
    tbl["delta"] = (tbl.time - tbl.time.iloc[0]).dt.total_seconds()
    tbl = tbl.set_index(tbl["delta"])

    power = tbl["sorensen850_manual"].mean()
    T_start = tbl["lakeshore336_temp_C_T"].iloc[0]
    T_stop = tbl["lakeshore336_temp_C_T"].iloc[-1]

    out = path / f"power_{power:.2f}-Tstart_{T_start:.2f}-Tstop_{T_stop:.2f}.csv"
    tbl[["lakeshore336_temp_C_T"]].to_csv(out)

    return tbl


def write_calibration_data_to_csv_and_make_tom_sad(
    uid_list, *, fname=None, stream_name="primary"
):
    if len(uid_list) and isinstance(uid_list[0], str):
        headers = [db[uid] for uid in uid_list]
    else:
        headers = uid_list
    headers = sorted(headers, key=lambda h: h.start["time"])

    merged_table = pd.concat([h.table(stream_name=stream_name) for h in headers])
    dt = (merged_table["time"] - merged_table["time"].iloc[0]).dt.total_seconds()
    dt.name = "delta_time"
    merged_table = merged_table.set_index(dt)

    if fname is not None:
        merged_table.to_csv(fname)
    return merged_table


from bluesky.utils import RunEngineControlException


def power_calibration_ramp(power_levels, *, hold_time, n_per_hold=10, path):
    ramp_uid = str(uuid.uuid4())
    out_uids = []

    def inner():
        for p in power_levels:
            yield from bps.mv(sorensen850_manual, p)
            try:
                uid = yield from bp.count(
                    [lakeshore336, sorensen850_manual],
                    num=n_per_hold,
                    delay=hold_time / n_per_hold,
                    md={"ramp_uid": ramp_uid, "purpose": "sorensen calibration"},
                )
                out_uids.append(uid)
            except RunEngineControlException:
                raise
            except Exception as e:
                # We want to prioritize this not crashing over night
                print(e)
                continue
            else:
                write_calibration_data_to_csv_and_make_tom_sad(out_uids, path)
        return out_uids

    def cleanup():
        yield from bps.mv(sorensen850_manual, 0)

    return (yield from bpp.finalize_wrapper(inner(), cleanup))


class RampControl(Device):
    delta = Cpt(EpicsSignal, "RampDelta")
    done = Cpt(EpicsSignal, "RampDone-Cmd")
    take_xrd = Cpt(EpicsSignal, "TakeXRD-Cmd")


ramp_control = RampControl("OvenRampControl:", name="ramp_control")

try:
    from bluesky.plan_stubs import rd
except ImportError:

    def rd(obj, *, default_value=0):
        """Reads a single-value non-triggered object

        This is a helper plan to get the scalar value out of a Device
        (such as an EpicsMotor or a single EpicsSignal).

        For devices that have more than one read key the following rules are used:

        - if exactly 1 field is hinted that value is used
        - if no fields are hinted and there is exactly 1 value in the
        reading that value is used
        - if more than one field is hinted an Exception is raised
        - if no fields are hinted and there is more than one key in the reading an
        Exception is raised

        The devices is not triggered and this plan does not create any Events

        Parameters
        ----------
        obj : Device
            The device to be read

        default_value : Any
            The value to return when not running in a "live" RunEngine.
            This come ups when ::

            ret = yield Msg('read', obj)
            assert ret is None

            the plan is passed to `list` or some other iterator that
            repeatedly sends `None` into the plan to advance the
            generator.

        Returns
        -------
        val : Any or None
            The "single" value of the device

        """
        hints = getattr(obj, "hints", {}).get("fields", [])
        if len(hints) > 1:
            msg = (
                f"Your object {obj} ({obj.name}.{getattr(obj, 'dotted_name', '')}) "
                f"has {len(hints)} items hinted ({hints}).  We do not know how to "
                "pick out a single value.  Please adjust the hinting by setting the "
                "kind of the components of this device or by rd ing one of it's components"
            )
            raise ValueError(msg)
        elif len(hints) == 0:
            hint = None
            if hasattr(obj, "read_attrs"):
                if len(obj.read_attrs) != 1:
                    msg = (
                        f"Your object {obj} ({obj.name}.{getattr(obj, 'dotted_name', '')}) "
                        f"and has {len(obj.read_attrs)} read attrs.  We do not know how to "
                        "pick out a single value.  Please adjust the hinting/read_attrs by "
                        "setting the kind of the components of this device or by rd ing one "
                        "of its components"
                    )

                    raise ValueError(msg)
        # len(hints) == 1
        else:
            (hint,) = hints

        ret = yield from read(obj)

        # list-ify mode
        if ret is None:
            return default_value

        if hint is not None:
            return ret[hint]["value"]

        # handle the no hint 1 field case
        try:
            (data,) = ret.values()
        except ValueError as er:
            msg = (
                f"Your object {obj} ({obj.name}.{getattr(obj, 'dotted_name', '')}) "
                f"and has {len(ret)} read values.  We do not know how to pick out a "
                "single value.  Please adjust the hinting/read_attrs by setting the "
                "kind of the components of this device or by rd ing one of its components"
            )

            raise ValueError(msg) from er
        else:
            return data["value"]


from dataclasses import dataclass


@dataclass(frozen=True)
class MotorPositions:
    beamstop_x: float
    beamstop_y: float
    detector: float


near_positions = MotorPositions(
    beamstop_x=-17.02152375, beamstop_y=0.717885, detector=3857.0
)
far_positions = MotorPositions(
    beamstop_x=-16.541525, beamstop_y=0.437885, detector=4973.0
)

from xpdacq.beamtime import close_shutter_stub


def power_ramp_controlled(
    *,
    min_power_pct: float = 0,
    max_power_pct: float = 1,  # max 100
    exposure: float,
    n_per_step=1,
    beamtime,
    xrd_sample_name: str,
    pdf_sample_name: str,
    near_positions,
    far_positions,
    diagostic_T_file=None,
    ramp_uid=None,
):
    """
    Plan to take externally controlled temperature ramps.

    This plan consults two PVs to determine the current ramp rate (delta) and
    if enough data has been collected and we should exit (more graceful than ctrl-C).

    At each hold point *n_per_point* sets of xrd and pdf will be taken.  The
    hold time per temperature will be approximately
    
        hold_time = (2*exposure + 70)*n_per_point

    Parameters
    ----------
    min_power_pct : float
        The minimum power (as a perentage) to give the heater
    max_power_pct : float
        The maxmimum power (as a percentage) to give the heater
    exposure : float
        Exposure time in seconds for each shot
    n_per_step : int, optional
        The number of exposures to take at each power step
    beamtime : xpdacq.xpdacq.Beamtime
        Used to get the sample meta-data
    xrd_sample_name : str
        Looked up in beamtime to get sample meta-data
    pdf_sample_same : str
        Looked up in beamtime to get sample meta-data
    near_positions, far_positions : MotorPositions
        The location of the beamstop and detector for "near" (PDF) and "far" (XRD)
        measurements
    diagsostic_T_file : Path
        If you must.
     """
    if ramp_uid is None:
        ramp_uid = str(uuid.uuid4())
    xrd_sample = beamtime.samples[xrd_sample_name]
    pdf_sample = beamtime.samples[pdf_sample_name]

    detector_motor = Det_1_Z
    beam_stop = BStop1

    baseline_detectors = [
        lakeshore336,
        ring_current,
        beam_stop,
        detector_motor,
        Grid_X,
        Grid_Y,
        Grid_Z,
        sorensen850_manual,
    ]
    main_detectors = [pe1c, sorensen850_manual]

    motor_snap_shot_for_dan = {
        k: globals()[k].read() for k in ["Grid_X", "Grid_Y", "Grid_Z"]
    }

    def collect_cycle(ramp_phase, delta=0):
        # PDF measurement
        print("/n/nmoving to PDF distance/n")
        yield from bps.mv(
            beam_stop.x,
            near_positions.beamstop_x,
            beam_stop.y,
            near_positions.beamstop_y,
            detector_motor,
            near_positions.detector,
        )
        pdf_uid = yield from bpp.baseline_wrapper(
            simple_ct(
                main_detectors,
                md={
                    "ramp_uid": ramp_uid,
                    "ramp_phase": ramp_phase,
                    **pdf_sample,
                    **motor_snap_shot_for_dan,
                    "delta": delta,
                },
                exposure=exposure,
            ),
            baseline_detectors,
        )
        yield from close_shutter_stub()
        # XRD measurement
        print("/n/nmoving to XRD position/n")
        take_xrd = yield from rd(ramp_control.take_xrd)
        if take_xrd:
            yield from bps.mv(
                beam_stop.x,
                far_positions.beamstop_x,
                beam_stop.y,
                far_positions.beamstop_y,
                detector_motor,
                far_positions.detector,
            )
            xrd_uid = yield from bpp.baseline_wrapper(
                simple_ct(
                    main_detectors,
                    md={
                        "ramp_uid": ramp_uid,
                        "ramp_phase": ramp_phase,
                        **xrd_sample,
                        **motor_snap_shot_for_dan,
                    },
                    exposure=exposure,
                ),
                baseline_detectors,
            )
            yield from close_shutter_stub()
        return []

    uids = []

    yield from bps.mv(ramp_control.done, 0)

    p = yield from rd(sorensen850_manual, default_value=min_power_pct)
    print(f"starting at power {p}")
    yield from bps.mv(sorensen850_manual, p)

    # for reasons TAC does not understand this is returning [None, None]
    # suspect it is due to one of the xpdacq wrappers not forwarding returs?
    data_uids = yield from collect_cycle("initial")
    uids.extend(data_uids)

    done = yield from rd(ramp_control.done, default_value=True)
    while not done:
        delta = yield from rd(ramp_control.delta)
        if delta > 0:
            ramp_phase = "rising"
        elif delta < 0:
            ramp_phase = "falling"
        else:
            ramp_phase = "holding"

        p = np.clip(p + delta, min_power_pct, max_power_pct)
        print(f"\n\n moving to {p} with {delta} step")

        yield from bps.mv(sorensen850_manual, p)

        for j in range(n_per_step):
            print(
                "\n\ntemperature is currently "
                + str(lakeshore336.read()["lakeshore336_temp_C_T"]["value"])
            )
            print("on step " + str(j) + " of " + str(n_per_step))
            data_uids = yield from collect_cycle(ramp_phase, delta)
            uids.extend(data_uids)
            if diagostic_T_file is not None:

                write_calibration_data_to_csv_and_make_tom_sad(
                    list(db(ramp_uid=ramp_uid)),
                    fname=diagostic_T_file,
                    stream_name="baseline",
                )
        done = yield from rd(ramp_control.done, default_value=True)

    uids.append((yield from collect_cycle("final")))
    return uids


# TODO reuse the code from above, but copy-paste for not to be sure
# we do not introduce bugs while refactoring.
def power_ramp_sequence(
    *,
    power_pct_seq,
    exposure: float,
    n_per_step=1,
    beamtime,
    xrd_sample_name: str,
    pdf_sample_name: str,
    near_positions,
    far_positions,
    diagostic_T_file=None,
):
    """
    Plan to take externally controlled temperature ramps.

    This plan consults two PVs to determine the current ramp rate (delta) and
    if enough data has been collected and we should exit (more graceful than ctrl-C).

    At each hold point *n_per_point* sets of xrd and pdf will be taken.  The
    hold time per temperature will be approximately
    
        hold_time = (2*exposure + 70)*n_per_point

    Parameters
    ----------
    power_pct : Iterable[float]
        Sequence of power precentages
    exposure : float
        Exposure time in seconds for each shot
    n_per_step : int, optional
        The number of exposures to take at each power step
    beamtime : xpdacq.xpdacq.Beamtime
        Used to get the sample meta-data
    xrd_sample_name : str
        Looked up in beamtime to get sample meta-data
    pdf_sample_same : str
        Looked up in beamtime to get sample meta-data
    near_positions, far_positions : MotorPositions
        The location of the beamstop and detector for "near" (PDF) and "far" (XRD)
        measurements
    diagsostic_T_file : Path
        If you must.
     """
    ramp_uid = str(uuid.uuid4())
    xrd_sample = beamtime.samples[xrd_sample_name]
    pdf_sample = beamtime.samples[pdf_sample_name]

    detector_motor = Det_1_Z
    beam_stop = BStop1

    baseline_detectors = [
        lakeshore336,
        ring_current,
        beam_stop,
        detector_motor,
        Grid_X,
        Grid_Y,
        Grid_Z,
        sorensen850_manual,
    ]
    main_detectors = [pe1c, sorensen850_manual]

    motor_snap_shot_for_dan = {
        k: globals()[k].read() for k in ["Grid_X", "Grid_Y", "Grid_Z"]
    }

    def collect_cycle(ramp_phase, delta=0):
        # PDF measurement
        print("\n\nmoving to PDF distance\n")
        yield from bps.mv(
            beam_stop.x,
            near_positions.beamstop_x,
            beam_stop.y,
            near_positions.beamstop_y,
            detector_motor,
            near_positions.detector,
        )
        pdf_uid = yield from bpp.baseline_wrapper(
            simple_ct(
                main_detectors,
                md={
                    "ramp_uid": ramp_uid,
                    "ramp_phase": ramp_phase,
                    **pdf_sample,
                    **motor_snap_shot_for_dan,
                    "delta": delta,
                },
                exposure=exposure,
            ),
            baseline_detectors,
        )
        yield from close_shutter_stub()
        take_xrd = yield from rd(ramp_control.take_xrd)
        if take_xrd:
            # XRD measurement
            print("\n\nmoving to XRD position\n")
            yield from bps.mv(
                beam_stop.x,
                far_positions.beamstop_x,
                beam_stop.y,
                far_positions.beamstop_y,
                detector_motor,
                far_positions.detector,
            )
            xrd_uid = yield from bpp.baseline_wrapper(
                simple_ct(
                    main_detectors,
                    md={
                        "ramp_uid": ramp_uid,
                        "ramp_phase": ramp_phase,
                        **xrd_sample,
                        **motor_snap_shot_for_dan,
                    },
                    exposure=exposure,
                ),
                baseline_detectors,
            )
            yield from close_shutter_stub()
        return []

    uids = []

    first_power, power_seq_tail = power_pct_seq

    yield from bps.mv(sorensen850_manual, first_power)

    # for reasons TAC does not understand this is returning [None, None]
    # suspect it is due to one of the xpdacq wrappers not forwarding returs?
    data_uids = yield from collect_cycle("initial")
    uids.extend(data_uids)

    last_power = first_power
    for p in power_seq_tail:
        delta = p - last_power
        last_power = p
        if delta > 0:
            ramp_phase = "rising"
        elif delta < 0:
            ramp_phase = "falling"
        else:
            ramp_phase = "holding"

        print(f"\n\n!!Moving to power {p} with delta {delta}")
        yield from bps.mv(sorensen850_manual, p)

        for j in range(n_per_step):
            print(
                "/n/ntemperature is currently "
                + str(lakeshore336.read()["lakeshore336_temp_C_T"]["value"])
            )
            print("on step " + str(j) + " of " + str(n_per_step))
            data_uids = yield from collect_cycle(ramp_phase, delta)
            uids.extend(data_uids)
            if diagostic_T_file is not None:

                write_calibration_data_to_csv_and_make_tom_sad(
                    list(db(ramp_uid=ramp_uid)),
                    fname=diagostic_T_file,
                    stream_name="baseline",
                )

    uids.extend((yield from collect_cycle("final")))
    return uids


# TODO reuse the code from above, but copy-paste for not to be sure
# we do not introduce bugs while refactoring.
def power_ramp_T_threshold(
    *,
    start_power_pct,
    max_temperature,
    delta_power,
    max_power_pct,
    exposure: float,
    n_per_step=1,
    beamtime,
    xrd_sample_name: str,
    pdf_sample_name: str,
    near_positions,
    far_positions,
    diagostic_T_file=None,
):
    """
    Plan to take externally controlled temperature ramps.

    This plan consults two PVs to determine the current ramp rate (delta) and
    if enough data has been collected and we should exit (more graceful than ctrl-C).

    At each hold point *n_per_point* sets of xrd and pdf will be taken.  The
    hold time per temperature will be approximately
    
        hold_time = (2*exposure + 70)*n_per_point

    Parameters
    ----------
    exposure : float
        Exposure time in seconds for each shot
    n_per_step : int, optional
        The number of exposures to take at each power step
    beamtime : xpdacq.xpdacq.Beamtime
        Used to get the sample meta-data
    xrd_sample_name : str
        Looked up in beamtime to get sample meta-data
    pdf_sample_same : str
        Looked up in beamtime to get sample meta-data
    near_positions, far_positions : MotorPositions
        The location of the beamstop and detector for "near" (PDF) and "far" (XRD)
        measurements
    diagsostic_T_file : Path
        If you must.
     """
    ramp_uid = str(uuid.uuid4())
    xrd_sample = beamtime.samples[xrd_sample_name]
    pdf_sample = beamtime.samples[pdf_sample_name]

    detector_motor = Det_1_Z
    beam_stop = BStop1

    baseline_detectors = [
        lakeshore336,
        ring_current,
        beam_stop,
        detector_motor,
        Grid_X,
        Grid_Y,
        Grid_Z,
        sorensen850_manual,
    ]
    main_detectors = [pe1c, sorensen850_manual]

    motor_snap_shot_for_dan = {
        k: globals()[k].read() for k in ["Grid_X", "Grid_Y", "Grid_Z"]
    }

    def collect_cycle(ramp_phase, delta=0):
        # PDF measurement
        print("\n\nmoving to PDF distance\n")
        yield from bps.mv(
            beam_stop.x,
            near_positions.beamstop_x,
            beam_stop.y,
            near_positions.beamstop_y,
            detector_motor,
            near_positions.detector,
        )
        pdf_uid = yield from bpp.baseline_wrapper(
            simple_ct(
                main_detectors,
                md={
                    "ramp_uid": ramp_uid,
                    "ramp_phase": ramp_phase,
                    **pdf_sample,
                    **motor_snap_shot_for_dan,
                    "delta": delta,
                },
                exposure=exposure,
            ),
            baseline_detectors,
        )
        yield from close_shutter_stub()
        take_xrd = yield from rd(ramp_control.take_xrd)
        if take_xrd:
            # XRD measurement
            print("\n\nmoving to XRD position\n")
            yield from bps.mv(
                beam_stop.x,
                far_positions.beamstop_x,
                beam_stop.y,
                far_positions.beamstop_y,
                detector_motor,
                far_positions.detector,
            )
            xrd_uid = yield from bpp.baseline_wrapper(
                simple_ct(
                    main_detectors,
                    md={
                        "ramp_uid": ramp_uid,
                        "ramp_phase": ramp_phase,
                        **xrd_sample,
                        **motor_snap_shot_for_dan,
                    },
                    exposure=exposure,
                ),
                baseline_detectors,
            )
            yield from close_shutter_stub()
        return []

    uids = []

    p = start_power_pct

    yield from bps.mv(sorensen850_manual, p)

    # for reasons TAC does not understand this is returning [None, None]
    # suspect it is due to one of the xpdacq wrappers not forwarding returs?
    data_uids = yield from collect_cycle("initial")
    uids.extend(data_uids)

    reversed = False

    delta = delta_power
    while True:
        p = np.clip(p + delta, 0, max_power_pct)
        T = yield from rd(lakeshore336)
        if T > max_temperature and not reversed:
            delta = -delta
        if delta > 0:
            ramp_phase = "rising"
        elif delta < 0:
            ramp_phase = "falling"
        else:
            ramp_phase = "holding"

        print(f"\n\n!!Moving to power {p} with delta {delta}")
        yield from bps.mv(sorensen850_manual, p)

        for j in range(n_per_step):
            print(
                "\n\ntemperature is currently "
                + str(lakeshore336.read()["lakeshore336_temp_C_T"]["value"])
            )
            print("on step " + str(j) + " of " + str(n_per_step))
            data_uids = yield from collect_cycle(ramp_phase, delta)
            uids.extend(data_uids)
            if diagostic_T_file is not None:

                write_calibration_data_to_csv_and_make_tom_sad(
                    list(db(ramp_uid=ramp_uid)),
                    fname=diagostic_T_file,
                    stream_name="baseline",
                )
        if p <= 0:
            break

    uids.extend((yield from collect_cycle("final")))
    return uids


def bring_to_temperature(power_supply, thermo, *, out_path):
    first_time = None

    def writer_call_back(name, doc):
        nonlocal first_time

        if name != "event":
            return
        if first_time is None:
            first_time = doc["time"]
        with open(out_path, "a+") as fout:
            data = [
                str(doc["data"][k])
                for k in ["sorensen850_manual", "lakeshore336_temp_C_T"]
            ]
            data_str = ",".join(data)
            fout.write(f'{doc["time"] - first_time},{data_str}\n')

    condition_time = 5 * 60
    condition_steps = 15
    sub_condition_time = condition_time / condition_steps

    condition_temperature_step = 50

    def condition_loop():
        print(f"entering {condition_time}s hold")
        for i in range(condition_steps):
            print(f"   stage {i} / {condition_steps}")
            yield from bps.trigger_and_read([power_supply, thermo])
            yield from bps.sleep(sub_condition_time)
        yield from bps.trigger_and_read([power_supply, thermo])

    @bpp.subs_decorator(writer_call_back)
    @bpp.run_decorator()
    def inner():
        yield from bps.trigger_and_read([power_supply, thermo])
        for p in np.arange(2.5, 30.0001, 0.1):
            yield from bps.mv(power_supply, p)
            yield from bps.checkpoint()
            yield from bps.sleep(5)
            yield from bps.trigger_and_read([power_supply, thermo])

        yield from condition_loop()

        T = yield from rd(thermo)
        t_target = T + condition_temperature_step
        p_cur = yield from rd(power_supply)
        while t_target < 1000:

            while T < t_target:
                p_cur += 0.1
                yield from bps.mv(power_supply, p_cur)
                yield from bps.checkpoint()
                yield from bps.sleep(5)
                yield from bps.trigger_and_read([power_supply, thermo])
                T = yield from rd(thermo)

            t_target += condition_temperature_step

            yield from condition_loop()
            print(f"new_target {t_target}")

    ret = yield from inner()
    return ret
