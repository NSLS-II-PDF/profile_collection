#!/usr/bin/env python3
from textwrap import dedent

from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class SimpleIOC(PVGroup):
    """
    An IOC with three uncoupled read/writable PVs

    Scalar PVs
    ----------
    A (int)
    B (float)

    Vectors PVs
    -----------
    C (vector of int)
    """

    done = pvproperty(
        value=0,
        doc="An integer to track if the ramp should be done.",
        name="RampDone-Cmd",
    )
    delta = pvproperty(value=0.1, doc="The delta of the ramp rate.", name="RampDelta")


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="OvenRampControl:", desc=dedent(SimpleIOC.__doc__)
    )
    ioc = SimpleIOC(**ioc_options)
    run(ioc.pvdb, **run_options)
