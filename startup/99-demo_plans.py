from dataclasses import dataclass
import bluesky.plan_stubs as bps


def move_det(x: float, y: float, z: float):
    yield from bps.mv(Det_1_X, x, Det_2_y, y, Det_1_Z, z)


@dataclass
class SamplePos:
    x: float
    y: float


SAMPLE_POSITONS = {
    # 'a': SamplePos(0, 0),
}


def move_to_sample(name: str):
    target_pos = SAMPLE_POSITONS[name]
    yield from bps.mv(Grid_X, target_pos.x, Grid_Y, target_pos.y)

