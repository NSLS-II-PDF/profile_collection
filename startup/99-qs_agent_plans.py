
def agent_sample_count(motor, position: float, exposure: float, *, sample_number: int, md=None):
    yield from bps.mv(motor, position)
    _md = dict(
        Grid_X=Grid_X.read(),
        Grid_Y=Grid_Y.read(),
        Grid_Z=Grid_Z.read(),
        Det_1_X=Det_1_X.read(),
        Det_1_Y=Det_1_Y.read(),
        Det_1_Z=Det_1_Z.read(),
        ring_current=ring_current.read(),
        BStop1=BStop1.read(),
    )
    _md.update(get_metadata_for_sample_number(bt, sample_number))
    _md.update(md or {})
    yield from simple_ct([pe1c], exposure, md=_md)

               
@bpp.run_decorator(md={})
def agent_driven_nap(delay: float, *, delay_kwarg: float = 0):
    """Ensuring we can auto add 'agent_' plans and use args/kwargs"""
    if delay_kwarg:
        yield from bps.sleep(delay_kwarg)
    else:
        yield from bps.sleep(delay)

               
def agent_print_glbl_val(key: str):
    """
    Get common global values from a namespace dictionary.
    Keys
    ---
    frame_acq_time : Frame rate acquisition time
    dk_window : dark window time
    """
    print(glbl[key])
    yield from bps.null()


def agent_set_glbl_val(key: str, val: float):
    """
    Set common global values from a namespace dictionary.
    Keys
    ---
    frame_acq_time : Frame rate acquisition time
    dk_window : dark window time
    """
    glbl[key] = val
    yield from bps.null()
