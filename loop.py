from pymeasure.instruments.keithley import Keithley2400
import numpy as np
from time import sleep
import matplotlib.pyplot as plt

def initKeithley():
    keithley = Keithley2400("GPIB::16")
    keithley.reset()
            # setting current params
            # self.keithley.use_front_terminals()
    keithley.use_rear_terminals()
    #keithley.use_front_terminals()
    keithley.apply_current(0.05, 4)
    keithley.wires = 4  # set to 4 wires
            # self.keithley.compliance_voltage = V_comp
    keithley.source_current = 0
    keithley.auto_zero = False
            # setting voltage read params
    keithley.measure_voltage(2, 0.1, True)
    keithley.write(":SYST:BEEP:STAT OFF")
    return keithley


keithley = initKeithley()
Voltages = []
I = np.linspace(-82,82,100)
for _I in I:
    keithley.source_current = _I/1000
    keithley.enable_source()
    #sleep(0.01)
    Voltages.append(keithley.voltage)


    print(_I,Voltages[-1])
    #sleep(0.01)
keithley.disable_source()

np.savetxt(r"D:\SES_1.9.1_Win64_Package\SES_1.9.1_Win64\Factory\2023\June\CIFA\electrical\New folder\BIN117A_afterCleave_222.csv",np.vstack((I,Voltages)).T,delimiter=",")
plt.plot(I,Voltages,'.')
plt.grid()
plt.xlabel("I [mA]")
plt.ylabel("V [voltage]")
plt.show()