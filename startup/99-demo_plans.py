from dataclasses import dataclass
import bluesky.plan_stubs as bps
from xpdacq.xpdacq import translate_to_sample as get_metadata_for_sample_number
import itertools


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
        beamstop_x=-16.44653, beamstop_y=3.7878875, detector=3700.0
    ),
    "far": DetectorConfiguration(
        beamstop_x=-16.44653, beamstop_y=3.7878875, detector=4700.0
    ),
}


def move_det(x: float = None, y: float = None, z: float = None):
    """
    Move the detector to the given (x, y, z)

    """
    args = tuple(
        itertools.chain(
            (m, t)
            for m, t in zip([Det_1_X, Det_1_Y, Det_1_Z], [x, y, z])
            if t is not None
        )
    )
    yield from bps.mv(*args)


def move_sample(x: float = None, y: float = None, z: float = None):
    """
    Move the detector to the given (x, y, z)

    """
    args = tuple(
        itertools.chain(
            (m, t) for m, t in zip([Grid_X, Grid_Y, Grid_Z], [x, y, z]) if t is not None
        )
    )
    yield from bps.mv(*args)


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


def sample_aware_count(sample_num: int, exposure: float, *, md=None):
    """
    A wrapper around count that tries to mimic xpdacq.

    """
    _md = get_metadata_for_sample_number(bt, sample_num)
    _md.update(md or {})
    yield from simple_ct([pe1c], exposure, md=_md)


fake_db = {
    0: {
        "xpdacq_number": 0,
        "detector_position": "far",
        "jog_start": 936.0 - 0.0,
        "jog_stop": 936.0 + 0.0,
        "x": 45.26912,
    }
}


def _df_to_fake_db(df):
    key_map = {
        "xpdacq_number": "xpdacq_name_num",
        "x": "xpos",
        "jog_start": "ymin",
        "job_stop": "ymax",
        "detector_position": "det_pos",
    }

    return {
        ix: {dest: r[src] for dest, src in key_map.items()} for ix, r in df.iterrows()
    }


def _refresh_sample_database() -> dict:
    # target = '/nsls2/data/pdf/legacy/processed/xpdacq_data/user_data_Purdy_Fall2021_Brackets_307061_4b04ec0b_2021-10-11-0917/my_df2.xlsx'
    # return _df_to_fake_db(pd.read_excel(target))
    return fake_db


def _pdf_count(
    sample_number: str,
    exposure_time: float,
    *,
    sample_db: dict,
    z_for_move: float,
    z_for_data: float,
    md: dict,
    # detectors
    dets: list,
    # motors
    beam_stop: Device,
    detector_motor: EpicsMotor,
    sample_x: EpicsMotor,
    sample_y: EpicsMotor,
    sample_z: EpicsMotor,
    bt,
):
    # sample_db = _refresh_sample_database()
    sample_info = sample_db[sample_number]
    _md = get_metadata_for_sample_number(bt, sample_info["xpdacq_number"])
    _md["sample_info"] = sample_info
    _md.update(md or {})

    target_pos = DETECTOR_POSITIONS[sample_info["detector_position"]]
    yield from bps.mv(sample_z, z_for_move)
    yield from bps.mv(
        # beamstop and detector
        # TODO make beamstop optional
        beam_stop.x,
        target_pos.beamstop_x,
        beam_stop.y,
        target_pos.beamstop_y,
        detector_motor,
        target_pos.detector,
        # sample position
        sample_x,
        sample_info["x"],
        sample_y,
        sample_info["jog_start"],
    )
    yield from bps.mv(sample_z, z_for_data)
    yield from rocking_ct(
        dets,
        exposure_time,
        sample_y,
        sample_info["jog_start"],
        sample_info["jog_stop"],
        md=_md,
    )


def pdf_count(sample_number: int, exposure_time: float, *, md: dict = {}):
    yield from _pdf_count(
        sample_number=sample_number,
        exposure_time=exposure_time,
        sample_db=_refresh_sample_database(),
        z_for_data=909.83,
        z_for_move=909.83 + 15.0,
        md=md,
        #
        beam_stop=BStop1,
        detector_motor=Det_1_Z,
        sample_y=Grid_Y,
        sample_x=broadside45_shifter,
        sample_z=Grid_Z,
        bt=bt,
        dets=[pe1c],
    )

def take_a_nap(delay: float):
    yield from bps.sleep(delay)