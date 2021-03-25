from bluesky.utils import short_uid

def future_count(detectors, num=1, delay=None, *, per_shot=None, md=None):
    """
    Take one or more readings from detectors.
    Parameters
    ----------
    detectors : list
        list of 'readable' objects
    num : integer, optional
        number of readings to take; default is 1
        If None, capture data until canceled
    delay : iterable or scalar, optional
        Time delay in seconds between successive readings; default is 0.
    per_shot : callable, optional
        hook for customizing action of inner loop (messages per step)
        Expected signature ::
           def f(detectors: Iterable[OphydObj]) -> Generator[Msg]:
               ...
    md : dict, optional
        metadata
    Notes
    -----
    If ``delay`` is an iterable, it must have at least ``num - 1`` entries or
    the plan will raise a ``ValueError`` during iteration.
    """
    if num is None:
        num_intervals = None
    else:
        num_intervals = num - 1
    _md = {
        "detectors": [det.name for det in detectors],
        "num_points": num,
        "num_intervals": num_intervals,
        "plan_args": {"detectors": list(map(repr, detectors)), "num": num},
        "plan_name": "count",
        "hints": {},
    }
    _md.update(md or {})
    _md["hints"].setdefault("dimensions", [(("time",), "primary")])

    if per_shot is None:
        per_shot = bps.one_shot

    @bpp.stage_decorator(detectors)
    @bpp.run_decorator(md=_md)
    def inner_count():
        return (
            yield from bps.repeat(partial(per_shot, detectors), num=num, delay=delay)
        )

    return (yield from inner_count())


def _xpd_pre_plan(dets, exposure):
    """Handle detector exposure time + xpdan required metadata"""

    def configure_area_det(det, exposure):
        '''Configure an area detector in "continuous mode"'''

        def _check_mini_expo(exposure, acq_time):
            if exposure < acq_time:
                raise ValueError(
                    "WARNING: total exposure time: {}s is shorter "
                    "than frame acquisition time {}s\n"
                    "you have two choices:\n"
                    "1) increase your exposure time to be at least"
                    "larger than frame acquisition time\n"
                    "2) increase the frame rate, if possible\n"
                    "    - to increase exposure time, simply resubmit"
                    " the ScanPlan with a longer exposure time\n"
                    "    - to increase frame-rate/decrease the"
                    " frame acquisition time, please use the"
                    " following command:\n"
                    "    >>> {} \n then rerun your ScanPlan definition"
                    " or rerun the xrun.\n"
                    "Note: by default, xpdAcq recommends running"
                    "the detector at its fastest frame-rate\n"
                    "(currently with a frame-acquisition time of"
                    "0.1s)\n in which case you cannot set it to a"
                    "lower value.".format(
                        exposure,
                        acq_time,
                        ">>> glbl['frame_acq_time'] = 0.5  #set" " to 0.5s",
                    )
                )

        # todo make
        ret = yield from bps.read(det.cam.acquire_time)
        if ret is None:
            acq_time = 1
        else:
            acq_time = ret[det.cam.acquire_time.name]["value"]
        _check_mini_expo(exposure, acq_time)
        if hasattr(det, "images_per_set"):
            # compute number of frames
            num_frame = np.ceil(exposure / acq_time)
            yield from bps.mov(det.images_per_set, num_frame)
        else:
            # The dexela detector does not support `images_per_set` so we just
            # use whatever the user asks for as the thing
            # TODO: maybe put in warnings if the exposure is too long?
            num_frame = 1
        computed_exposure = num_frame * acq_time

        # print exposure time
        print(
            "INFO: requested exposure time = {} - > computed exposure time"
            "= {}".format(exposure, computed_exposure)
        )
        return num_frame, acq_time, computed_exposure

    # setting up area_detector
    for ad in (d for d in dets if hasattr(d, "cam")):
        (num_frame, acq_time, computed_exposure) = yield from configure_area_det(
            ad, exposure
        )
    else:
        acq_time = 0
        computed_exposure = exposure
        num_frame = 0

    sp = {
        "time_per_frame": acq_time,
        "num_frames": num_frame,
        "requested_exposure": exposure,
        "computed_exposure": computed_exposure,
        "type": "ct",
        "uid": str(uuid.uuid4()),
        "plan_name": "ct",
    }

    # update md
    _md = {"sp": sp, **{f"sp_{k}": v for k, v in sp.items()}}

    return _md


def rocking_ct(dets, exposure, motor, start, stop, *, num=1, md=None):
    """Take a count while "rocking" the y-position"""
    _md = md or {}
    sp_md = yield from _xpd_pre_plan(dets, exposure)
    _md.update(sp_md)

    @bpp.reset_positions_decorator([motor.velocity])
    def per_shot(dets):
        nonlocal start, stop
        yield from bps.mv(motor, start) # got to initial position
        yield from bps.mv(motor.velocity, abs(stop - start) / exposure) # set velocity
        gp = short_uid("rocker")
        yield from bps.abs_set(motor, stop, group=gp) # set motor to move towards end
        yield from bps.trigger_and_read(dets) # collect off detector
        yield from bps.wait(group=gp)
        start, stop = stop, start

    return (yield from future_count(dets, md=_md, per_shot=per_shot, num=num))

def jog(exposure_s, motor, start, stop):
    """ pass total exposure time (in seconds), motor name (i.e. Grid_Y), start and stop positions for the motor."""
    yield from rocking_ct([pe1c], exposure_s, motor, start, stop)
        

