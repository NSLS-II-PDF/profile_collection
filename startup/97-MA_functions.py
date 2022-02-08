"Define Beamline Modes"


def beam22slit():
    # print("Resetting white beam slits") 2021-3 values
    # wb_slits.inboard.move(-11.55)
    # wb_slits.outboard.move(-5.879)

    # print("Resetting Monochromator") # 2021-3 values
    # sbm.yaw.move(0.00012)
    # sbm.roll.move(0.0008)
    # sbm.pitch.move(-0.02827)
    # sbm.bend.move(2000.0084)
    # sbm.twist.move(0)

    print("Resetting Mirror")
    # Mirror_VFM.y_upstream.move(-1.2493) # 2021-3 values
    # Mirror_VFM.y_downstream_inboard.move(-0.3179)
    # Mirror_VFM.y_downstream_outboard.move(-0.0806)
    Mirror_VFM.bend_upstream.move(100)
    Mirror_VFM.bend_downstream.move(100)

    # print("Resetting BDM Slits")
    # bdm_slits.top.move(999.957)
    # bdm_slits.bottom.move(-94363.970)
    # bdm_slits.inboard.move(-7600.960)
    # bdm_slits.outboard.move(-4100.075)

    print("Resetting OCM Slits")
    ocm_slits.top.move(-765.286)
    ocm_slits.bottom.move(545.00)
    ocm_slits.outboard.move(2005.959)
    ocm_slits.inboard.move(-1939.037)

    print("Resetting Anti-scatter Slits")
    caput("XF:28ID1B-OP{Slt:AS-Ax:T}Mtr.VAL", -24.95948)  # Top
    caput("XF:28ID1B-OP{Slt:AS-Ax:B}Mtr.VAL", -31.49997)  # Bottom
    caput("XF:28ID1B-OP{Slt:AS-Ax:O}Mtr.VAL", -27.89998)  # Outboard
    caput("XF:28ID1B-OP{Slt:AS-Ax:I}Mtr.VAL", 6.09888)  # inboard
    print("Ready to go !")


def beam22():
    # print("Resetting white beam slits") 2021-3 values
    # wb_slits.inboard.move(-11.55)
    # wb_slits.outboard.move(-5.879)

    # print("Resetting Monochromator") # 2021-3 values
    # sbm.yaw.move(0.00012)
    # sbm.roll.move(0.0008)
    # sbm.pitch.move(-0.02827)
    # sbm.bend.move(2000.0084)
    # sbm.twist.move(0)

    print("Resetting Mirror")
    # Mirror_VFM.y_upstream.move(-1.2493) # 2021-3 values
    # Mirror_VFM.y_downstream_inboard.move(-0.3179)
    # Mirror_VFM.y_downstream_outboard.move(-0.0806)
    Mirror_VFM.bend_upstream.move(150)
    Mirror_VFM.bend_downstream.move(150)

    # print("Resetting BDM Slits")
    # bdm_slits.top.move(999.957)
    # bdm_slits.bottom.move(-94363.970)
    # bdm_slits.inboard.move(-7600.960)
    # bdm_slits.outboard.move(-4100.075)

    print("Resetting OCM Slits")
    ocm_slits.top.move(-765.286)
    ocm_slits.bottom.move(545.00)
    ocm_slits.outboard.move(2005.959)
    ocm_slits.inboard.move(-1939.037)

    print("Resetting Anti-scatter Slits")
    caput("XF:28ID1B-OP{Slt:AS-Ax:T}Mtr.VAL", -24.95948)  # Top
    caput("XF:28ID1B-OP{Slt:AS-Ax:B}Mtr.VAL", -31.49997)  # Bottom
    caput("XF:28ID1B-OP{Slt:AS-Ax:O}Mtr.VAL", -27.89998)  # Outboard
    caput("XF:28ID1B-OP{Slt:AS-Ax:I}Mtr.VAL", 6.09888)  # inboard
    print("Ready to go !")


def beam33():
    # print("Resetting white beam slits") 2021-3 values
    # wb_slits.inboard.move(-11.55)
    # wb_slits.outboard.move(-5.879)

    # print("Resetting Monochromator") # 2021-3 values
    # sbm.yaw.move(0.00012)
    # sbm.roll.move(0.0008)
    # sbm.pitch.move(-0.02827)
    # sbm.bend.move(2000.0084)
    # sbm.twist.move(0)

    print("Resetting Mirror")
    # Mirror_VFM.y_upstream.move(-1.2493) # 2021-3 values
    # Mirror_VFM.y_downstream_inboard.move(-0.3179)
    # Mirror_VFM.y_downstream_outboard.move(-0.0806)
    Mirror_VFM.bend_upstream.move(120)
    Mirror_VFM.bend_downstream.move(120)

    # print("Resetting BDM Slits")
    # bdm_slits.top.move(999.957)
    # bdm_slits.bottom.move(-94363.970)
    # bdm_slits.inboard.move(-7600.960)
    # bdm_slits.outboard.move(-4100.075)

    print("Resetting OCM Slits")
    ocm_slits.top.move(-765.286)
    ocm_slits.bottom.move(545.00)
    ocm_slits.outboard.move(2005.959)
    ocm_slits.inboard.move(-1939.037)

    print("Resetting Anti-scatter Slits")
    caput("XF:28ID1B-OP{Slt:AS-Ax:T}Mtr.VAL", -24.90948)  # Top
    caput("XF:28ID1B-OP{Slt:AS-Ax:B}Mtr.VAL", -31.44997)  # Bottom
    caput("XF:28ID1B-OP{Slt:AS-Ax:O}Mtr.VAL", -27.84998)  # Outboard
    caput("XF:28ID1B-OP{Slt:AS-Ax:I}Mtr.VAL", 6.19888)  # inboard
    print("Ready to go !")


def beam55():
    # print("Resetting white beam slits") 2021-3 values
    # wb_slits.inboard.move(-11.55)
    # wb_slits.outboard.move(-5.879)

    # print("Resetting Monochromator") # 2021-3 values
    # sbm.yaw.move(0.00012)
    # sbm.roll.move(0.0008)
    # sbm.pitch.move(-0.02827)
    # sbm.bend.move(2000.0084)
    # sbm.twist.move(0)

    print("Resetting Mirror")
    # Mirror_VFM.y_upstream.move(-1.2493) # 2021-3 values
    # Mirror_VFM.y_downstream_inboard.move(-0.3179)
    # Mirror_VFM.y_downstream_outboard.move(-0.0806)
    Mirror_VFM.bend_upstream.move(100)
    Mirror_VFM.bend_downstream.move(100)

    # print("Resetting BDM Slits")
    # bdm_slits.top.move(999.957)
    # bdm_slits.bottom.move(-94363.970)
    # bdm_slits.inboard.move(-7600.960)
    # bdm_slits.outboard.move(-4100.075)

    print("Resetting OCM Slits")
    ocm_slits.top.move(-665.286)
    ocm_slits.bottom.move(645.00)
    ocm_slits.outboard.move(2105.959)
    ocm_slits.inboard.move(-1839.037)

    print("Resetting Anti-scatter Slits")
    caput("XF:28ID1B-OP{Slt:AS-Ax:T}Mtr.VAL", -24.80948)  # Top
    caput("XF:28ID1B-OP{Slt:AS-Ax:B}Mtr.VAL", -31.34997)  # Bottom
    caput("XF:28ID1B-OP{Slt:AS-Ax:O}Mtr.VAL", -27.69998)  # Outboard
    caput("XF:28ID1B-OP{Slt:AS-Ax:I}Mtr.VAL", 6.29888)  # inboard
    print("Ready to go !")


def saxs():
    print("Resetting white beam slits")
    wb_slits.inboard.move(-13.6)
    wb_slits.outboard.move(-7.54218)

    print("Resetting Monochromator")
    sbm.yaw.move(0.0)
    sbm.roll.move(0.0)
    sbm.pitch.move(-0.05149)
    sbm.bend.move(1550)
    sbm.twist.move(-30)

    print("Resetting Mirror")
    Mirror_VFM.y_upstream.move(-0.7)
    Mirror_VFM.y_downstream_inboard.move(-0.02)
    Mirror_VFM.y_downstream_outboard.move(0.32)
    Mirror_VFM.bend_upstream.move(10)
    Mirror_VFM.bend_downstream.move(10)

    print("Resetting BDM Slits")
    # bdm_slits.top.move(999.957)
    # bdm_slits.bottom.move(-94363.970)
    # bdm_slits.inboard.move(-7600.960)
    # bdm_slits.outboard.move(-4100.075)

    print("Resetting OCM Slits")
    ocm_slits.top.move(-1065.0)
    ocm_slits.bottom.move(1955.0)
    ocm_slits.outboard.move(635.959)
    ocm_slits.inboard.move(-94.037)
    OCM_table.upstream_jack.move(4.14225)
    OCM_table.downstream_jack.move(-4.1700)
    OCM_table.X.move(-8.44701)
    print("Ready to go !")


def BDM_plot():
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import pylab as pl
    from PIL import Image
    import numpy as np
    import pylab

    img = Image.open("/nsls2/xf28id1/BDM_camera/BDM_ROI_000.tiff").convert("L")
    z = np.asarray(img)
    mydata = z[375:450:1, 550:850:1]  # y and x
    # mydata = z[164:300:1, 200:1000:1]
    fig = pl.figure(facecolor="w")
    ax1 = fig.add_subplot(1, 2, 1)
    im = ax1.imshow(mydata, interpolation="nearest", cmap=pl.cm.jet)
    ax1.set_title("2D")

    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    x, y = np.mgrid[: mydata.shape[0], : mydata.shape[1]]
    ax2.plot_surface(
        x,
        y,
        mydata,
        cmap=pl.cm.jet,
        rstride=1,
        cstride=1,
        linewidth=0.0,
        antialiased=False,
    )
    ax2.set_title("3D")
    # ax2.set_zlim3d(0,100)
    pl.show()


# ----------turbo() is a Temporary fix until auto turbo mode is implemented in the css layer---------
from epics import caget, caput

turbo_T = 110  # Turbo turning on temperature


def turbo():
    current_T = cryostream.T.get()
    tb = caget("XF:28ID1-ES:1{Env:01}Cmd:Turbo-Cmd")
    if current_T <= turbo_T and tb == 0:
        caput("XF:28ID1-ES:1{Env:01}Cmd:Turbo-Cmd", 1)
        time.sleep(2)
        caput("XF:28ID1-ES:1{Env:01}Cmd-Cmd", 20)
    if current_T >= turbo_T and tb == 1:
        caput("XF:28ID1-ES:1{Env:01}Cmd:Turbo-Cmd", 0)
        time.sleep(2)
        caput("XF:28ID1-ES:1{Env:01}Cmd-Cmd", 20)


# get direct beamcurrent
# def I0():
#    I0 = caget("SR:OPS-BI{DCCT:1}I:Real-I")

# ---------------------------function to display the dark subtracted last image ----------------------------------
from tifffile import imread, imshow, imsave


def lastimage(n):
    hdr = db[-n]
    for doc in hdr.documents(fill=True):
        data1 = doc[1].get("data")
        if data1 != None:
            light_img = data1["pe1c_image"]

    dark_uid = hdr.start.get("sc_dk_field_uid")
    dk_hdrs = db(uid=dark_uid)
    for dk_hdr in dk_hdrs:
        for doc in dk_hdr.documents(fill=True):
            dk_data1 = doc[1].get("data")
            if dk_data1 != None:
                dk_img = dk_data1["pe1c_image"]

    I = light_img - dk_img
    imshow(I, vmax=(I.sum() / (2048 * 2048)), cmap="jet")
    imsave(
        "/nsls2/xf28id1/xpdacq_data/user_data/tiff_base/" + "dark_sub_image" + ".tiff",
        light_img - dk_img,
    )
    imsave(
        "/nsls2/xf28id1/xpdacq_data/user_data/tiff_base/" + "dark_image" + ".tiff",
        dk_img,
    )
    imsave(
        "/nsls2/xf28id1/xpdacq_data/user_data/tiff_base/" + "light_image" + ".tiff",
        light_img,
    )


# ---------------------------------HAB T setpoint threshold--------------------------------------------
def HAB_Tset(t, threshold, settle_time):
    caput("XF:28ID1-ES:1{Env:05}LOOP1:SP", t)
    T_now = hotairblower.get()

    while T_now not in range(t - threshold, t + 2 * threshold):
        T_now = hotairblower.get()
        time.sleep(0.5)
    time.sleep(settle_time)


# ---------------------------------Magnet I setpoint threshold--------------------------------------------
def Magnet_Iset(i, settle_time):  # rounds up the setpoint to a integer thres
    RE(mv(magnet.setpoint, i))
    I_now = magnet.readback.get()

    while np.around(I_now) != i:
        I_now = magnet.readback.get()
        time.sleep(0.5)
    time.sleep(settle_time)


def Magnet_Iset2(i, thershold_1_D_point, settle_time):
    RE(mv(magnet.setpoint, i))
    I_now = magnet.readback.get()

    while (I_now * 10) not in range(
        np.around((i - thershold_1_D_point) * 10, 1),
        np.around((i + thershold_1_D_point) * 10, 1),
    ):
        I_now = magnet.readback.get()
        time.sleep(0.5)
    time.sleep(settle_time)


def Cryostat_CF(t, settle_time):  # rounds up the setpoint to a integer thres
    RE(mv(cryostat1, t))
    t_now = caget("XF:28ID1-ES1:LS335:{CryoStat}:IN2")

    while np.around(t_now) != i:
        t_now = caget("XF:28ID1-ES1:LS335:{CryoStat}:IN2")
        time.sleep(0.5)
    time.sleep(settle_time)


# ---------------------------------HAB T setpoint threshold--------------------------------------------
def Humidity_set(a, b, threshold, settle_time):
	RE(flow(a,b))
	H = readRH
	H_now = readRH(verbosity=2)

	while H_now not in range(H-threshold, H+2*threshold):
		H_now = readRH(verbosity=2)
		time.sleep(0.5)
	time.sleep(settle_time)

#---------------------------------Reaction cell--------------------------------------------
'''
def HAB_Tset(t, threshold, settle_time):
	caput("Set point PV", t)
	T_now = caget("Readback PV")

	while T_now not in range(t-threshold, t+2*threshold):
		T_now = caget("Readback PV")
		time.sleep(0.5)
	time.sleep(settle_time)
'''
