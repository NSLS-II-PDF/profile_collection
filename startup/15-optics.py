"Define motors related to optics"


class Slits(Device):
    top = Cpt(EpicsMotor, 'T}Mtr')
    bottom = Cpt(EpicsMotor, 'B}Mtr')
    inboard = Cpt(EpicsMotor, 'I}Mtr')
    outboard = Cpt(EpicsMotor, 'O}Mtr')
    ''' TODO : Add later
    xc = Cpt(EpicsMotor, 'XCtr}Mtr')
    xg = Cpt(EpicsMotor, 'XGap}Mtr')
    yc = Cpt(EpicsMotor, 'YCtr}Mtr')
    yg = Cpt(EpicsMotor, 'YGap}Mtr')
    '''

ocm_slits = Slits('XF:28ID1B-OP{Slt:2-Ax:', name='ocm_slits')  # OCM Slits
bdm_slits = Slits('XF:28ID1A-OP{Slt:1-Ax:', name='bdm_slits')  # BD Slits

class SideBounceMono(Device):
    x_wedgemount = Cpt(EpicsMotor, "X}Mtr")
    y_wedgemount = Cpt(EpicsMotor, "Y}Mtr")
    yaw = Cpt(EpicsMotor, "Yaw}Mtr")
    pitch = Cpt(EpicsMotor, "Pitch}Mtr")
    roll = Cpt(EpicsMotor, "Roll}Mtr")
    bend = Cpt(EpicsMotor, "Bend}Mtr")
    twist = Cpt(EpicsMotor, "Twist}Mtr")

sbm = SideBounceMono("XF:28ID1A-OP{Mono:SBM-Ax:", name='sbm')


class PDFShutter(EpicsSignal):

    def stop(self):
        self.set(0)

    def resume(self):
        self.set(1)


# Shutters:
fs = PDFShutter('XF:28ID1B-OP{PSh:1-Det:2}Cmd', name='fs')  # fast shutter


class Mirror(Device):
    y_upstream = Cpt(EpicsMotor, 'YU}Mtr')
    y_downstream_inboard = Cpt(EpicsMotor, 'YDI}Mtr')
    y_downstream_outboard = Cpt(EpicsMotor, 'YDO}Mtr')
    bend_upstream = Cpt(EpicsMotor, 'BndU}Mtr')
    bend_encoder = Cpt(EpicsSignalRO, 'BndU}Pos:Enc-I')
    bend_downstream = Cpt(EpicsMotor, 'BndD}Mtr')
    twist_encoder = Cpt(EpicsSignalRO, 'BndD}Pos:Enc-I')
    # TODO: add coordinated motions later:
    # y_upstream, y_downstream_inboard, y_downstream_outboard

Mirror_VFM = Mirror('XF:28ID1A-OP{Mir:VFM-Ax:', name='Mirror_VFM')

class OpticsTableADC(Device):
    upstream_jack_inboard = Cpt(EpicsMotor, 'YUI}Mtr')
    upstream_jack_outboard = Cpt(EpicsMotor, 'YUO}Mtr')
    downstream_jack_outboard = Cpt(EpicsMotor, 'YD}Mtr')
    X_upstream = Cpt(EpicsMotor, 'XU}Mtr')
    X_downstream = Cpt(EpicsMotor, 'XD}Mtr')
    Z = Cpt(EpicsMotor, 'Z}Mtr')

optics_table_adc = OpticsTableADC(prefix="XF:28ID1B-ES{Tbl:1-Ax:",
                                  name="optics_table_adc")

class SpinnerGoniohead(Device):
    X = Cpt(EpicsMotor, 'X}Mtr')
    Y = Cpt(EpicsMotor, 'Y}Mtr')
    Z = Cpt(EpicsMotor, 'Z}Mtr')
    Ry = Cpt(EpicsMotor, 'Ry}Mtr')

spinner_goniohead = SpinnerGoniohead(prefix="XF:28ID1B-ES{Stg:Smpl-Ax:",
                                     name="spinner_goniohead")
