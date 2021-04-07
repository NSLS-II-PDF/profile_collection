from dataclasses import dataclass
import bluesky.plan_stubs as bps
from xpdacq.xpdacq import translate_to_sample


@dataclass(frozen=True)
class SamplePos:
    x: float
    y: float


@dataclass(frozen=True)
class DetectorConfiguration:
    beamstop_x: float
    beamstop_y: float
    detector: float


SAMPLE_POSITONS = {
    # 'a': SamplePos(0, 0),
}

DETECTOR_POSITIONS = {
    "near": DetectorConfiguration(
        beamstop_x=-17.02152375, beamstop_y=0.717885, detector=3857.0
    ),
    "far": DetectorConfiguration(
        beamstop_x=-16.541525, beamstop_y=0.437885, detector=4973.0
    ),
}


def move_det(x: float = None, y: float = None, z: float = None):
    """
    Move the detector to the given (x, y, z)

    """
    yield from bps.mv(Det_1_X, x, Det_1_Y, y, Det_1_Z, z)


def move_sample(x: float = None, y: float = None, z: float = None):
    """
    Move the detector to the given (x, y, z)

    """
    yield from bps.mv(Grid_X, x, Grid_Y, y, Grid_Z, z)


def move_to_sample(name: str):
    sample_x = Grid_X
    sample_y = Grid_Y
    target_pos = SAMPLE_POSITONS[name]
    yield from bps.mv(sample_x, target_pos.x, sample_y, target_pos.y)


def move_to_det_config(name: str):

    detector_motor = Det_1_Z
    beam_stop = BStop1

    target_pos = DETECTOR_POSITIONS[name]
    yield from bps.mv(
        beam_stop.x,
        target_pos.beamstop_x,
        beam_stop.y,
        target_pos.beamstop_y,
        detector_motor,
        target_pos.detector,
    )


def sample_aware_count(dets, sample_num: int, exposure: float, *, md=None):
    """
    A wrapper around count that tries to mimic xpdacq.

    """
    _md = translate_to_sample(bt, sample_num)
    _md.update(md or {})
    yield from simple_ct(dets, exposure, md=_md)
