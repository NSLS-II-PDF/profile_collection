
def agent_sample_count(position: float, exposure: float, *, md=None):
    yield from bps.mv(Grid_X, position)
    _md = dict(Grid_X=Grid_X.read())
    _md.update(md or {})
    yield from simple_ct([pe1c], exposure, md=_md)


@bpp.run_decorator(md={})
def agent_driven_nap(delay: float, *, delay_kwarg: float = 0):
    """Ensuring we can auto add 'agent_' plans and use args/kwargs"""
    if delay_kwarg:
        yield from bps.sleep(delay_kwarg)
    else:
        yield from bps.sleep(delay)