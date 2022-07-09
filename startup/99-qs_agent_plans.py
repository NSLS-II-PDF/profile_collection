
def agent_sample_count(position: float, exposure: float, *, md=None):
    yield from bps.mv(Grid_X, position)
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
    _md.update(md or {})
    yield from simple_ct([pe1c], exposure, md=_md)

@bpp.run_decorator(md={})
def agent_driven_nap(delay: float, *, delay_kwarg: float = 0):
    """Ensuring we can auto add 'agent_' plans and use args/kwargs"""
    if delay_kwarg:
        yield from bps.sleep(delay_kwarg)
    else:
        yield from bps.sleep(delay)
