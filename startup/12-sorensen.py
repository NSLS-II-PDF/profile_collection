from ophyd import EpicsSignal
import numpy as np
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp


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


def write_calibration_data_to_csv_and_make_tom_sad(uid_list, *, fname=None):
    headers = [db[uid] for uid in uid_list]
    headers = sorted(headers, key=lambda h: h.start["time"])

    merged_table = pd.concat([h.table() for h in headers])
    merged_table["delta"] = (
        merged_table["time"] - merged_table["time"].iloc[0]
    ).dt.total_seconds()
    merged_table = merged_table.set_index(merged_table["delta"])

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


def power_ramp_controlled(
    *,
    min_power_pct: float = 0,
    max_power_pct: float = 1,  # max 100
    xrd_sample_name: str,
    pdf_sample_name: str,
    exposure: float,
    beamtime,
    n_per_step=1,
    near_positions,
    far_positions,
):
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
    ]
    main_detectors = [pe1c, sorensen850_manual]

    motor_snap_shot_for_dan = {
        k: globals()[k].read() for k in ["Grid_X", "Grid_Y", "Grid_Z"]
    }

    def collect_cycle(ramp_phase, delta=0):
        # PDF measurement
        yield from bps.mv(
            beam_stop.x,
            near_positions.beamstop_x,
            beam_stop.y,
            near_positions.beamstop_y,
            detector_motor,
            near_positions.detector,
        )
        yield from bpp.baseline_wrapper(
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
        # XRD measurement
        yield from bps.mv(
            beam_stop.x,
            far_positions.beamstop_x,
            beam_stop.y,
            far_positions.beamstop_y,
            detector_motor,
            far_positions.detector,
        )
        yield from bpp.baseline_wrapper(
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

    yield from bps.mv(ramp_control.done, 0)

    p = min_power_pct
    yield from bps.mv(sorensen850_manual, p)

    yield from collect_cycle("initial")

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

        yield from bps.mv(sorensen850_manual, p)

        for j in range(n_per_step):
            yield from collect_cycle(ramp_phase, delta)
        done = yield from rd(ramp_control.done, default_value=True)

    yield from bps.collect_cycle("final")

