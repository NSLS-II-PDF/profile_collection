from ophyd import Device, Component as Cpt, EpicsSignal
import time
import datetime


class RampControl(Device):
    delta = Cpt(EpicsSignal, "RampDelta")
    done = Cpt(EpicsSignal, "RampDone-Cmd")
    take_xrd = Cpt(EpicsSignal, "TakeXRD-Cmd")


temperature = EpicsSignal("XF:28ID1-ES{LS336:1-Chan:C}T-I")
ramp_control = RampControl("OvenRampControl:", name="ramp_control")
power_rbv = EpicsSignal("XF:28ID1-ES{LS336:1-Out:3}Out:Man-RB")
power_sp = EpicsSignal("XF:28ID1-ES{LS336:1-Out:3}Out:Man-SP")

print(f"{datetime.datetime.now()} Good morning! Robo-dan going to work!")

while True:
    T = temperature.get()
    if T is not None and T > 1025:
        break
    time.sleep(60)
    print(f"{datetime.datetime.now()} temperature at {T:.2f}, keep going!")

print(f"{datetime.datetime.now()} temperature at {T}, Done!!")

ramp_control.delta.put(0)
print(f"{datetime.datetime.now()}  holding for 5 minutes")
time.sleep(60 * 5)

print(f"{datetime.datetime.now()} starting cooling")
ramp_control.delta.put(-2.5)

while True:
    p = power_rbv.get()
    print(f"{datetime.datetime.now()} power currently at {p}, still cooling")
    if p < 1:
        break
    time.sleep(3 * 60)

time.sleep(5 * 60)
print(f"{datetime.datetime.now()} power low, declare done")
ramp_control.done.put(1)

time.sleep(5 * 60)
print(f"{datetime.datetime.now()} putting power to 0 just in case")
power_sp.put(0)
