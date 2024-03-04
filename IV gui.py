# -*- coding: utf-8 -*-
"""
Created on Tue May  9 14:35:48 2023

@author: kopel1
"""


import logging
from pymeasure.instruments.keithley import Keithley2400
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
import numpy as np
import sys
import tempfile
import random
from time import sleep
from pymeasure.log import console_log
from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Procedure, Results,unique_filename
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter
#k.current = 1
class RandomProcedure(Procedure):

    iterations = IntegerParameter('Loop Iterations', default=500)
    delay = FloatParameter('Delay Time', units='s', default=0.01)
    comp_volt = FloatParameter('Compliance Voltage', units='V', default=10)
    comp_current = FloatParameter('Compliance Current', units='A', default=0.2)
    start_current = FloatParameter("start current", units ='mA',default=-10)
    end_current = FloatParameter("end current", units ='mA',default=10)

    DATA_COLUMNS = ['I[mA]','V[mV]']
    def startup1(self):
        log.info("Setting the seed of the random number generator")

    def startup(self):
        log.info("start keithley setup.")
        self.keithley = Keithley2400("GPIB::16")
        self.keithley.reset()

        # self.keithley.use_front_terminals()
        self.keithley.use_rear_terminals()
        #keithley.use_front_terminals()
        self.keithley.apply_current(0.05, self.comp_volt)
        self.keithley.wires = 4  # set to 4 wires
        # self.keithley.compliance_voltage = V_comp
        self.keithley.source_current = 0
        self.keithley.auto_zero = False
            # setting voltage read params
        self.keithley.measure_voltage(2, 0.1, True)
        self.keithley.write(":SYST:BEEP:STAT OFF")

        log.info("keithley setup complete.")


    def execute1(self):
        log.info("Starting the loop of %d iterations" % self.iterations)
        #k.compliance_voltage = self.comp_volt
        #k.compliance_current = self.comp_current
        j=0
        for I in np.linspace(self.start_current,self.end_current,self.iterations):
           # k.apply_voltage = V
           #data = {
            #   'I': k.measure_current(),
             #  'dI/dV':
            data = {
                'I': I**2,
                'V': I
            }
            self.emit('results', data)
            log.debug("Emitting results: %s" % data)
            self.emit('progress', 100 * I / self.iterations)
            sleep(self.delay)
            j=j+1
            if self.should_stop():
                log.warning("Caught the stop flag in the procedure")
                break

    def execute(self):
        log.info("Starting the loop of %d iterations" % self.iterations)

        I = np.linspace(self.start_current,self.end_current,self.iterations)
        j=0
        for _I in I:  #_I is in mA!
           self.keithley.source_current = _I/1000 #Converting to keithley's Amps
           self.keithley.enable_source()
           V = self.keithley.voltage
           data = {'I[mA]': _I,'V[mV]': V*1000}
           self.emit('results', data)
           log.debug("Emitting results: %s" % data)
           self.emit('progress', j/len(I)*100 )
           j=j+1
           sleep(self.delay)
           if self.should_stop():
               self.keithley.disable_source()
               log.warning("Caught the stop flag in the procedure")
               break
        self.keithley.disable_source()


class MainWindow(ManagedWindow):

    def __init__(self):
        super().__init__(
            procedure_class=RandomProcedure,
            inputs=['iterations', 'delay','start_current','end_current','comp_current','comp_volt'],
            displays=['iterations', 'delay','start_current','end_current','comp_current','comp_volt'],
            y_axis='V[mV]',
            x_axis='I[mA]',
            directory_input= True
        )
        self.setWindowTitle('IV')

        self.filename = r'default_filename_delay{Delay Time:4f}s'   # Sets default filename
        self.directory = r'C:\Users\Scienta Omicron\OneDrive - Technion\ARPES scripts\RT\data'            # Sets default directory
        #self.store_measurement = False                              # Controls the 'Save data' toggle
        #self.file_input.extensions = ["csv", "txt", "data"]         # Sets recognized extensions, first entry is the default extension
        #self.file_input.filename_fixed = False                      # Controls whether the filename-field is frozen (but still displayed)

    def queue(self):
        if self.directory:
            filename = unique_filename(self.directory)
        else:
            filename = tempfile.mktemp()

        procedure = self.make_procedure()
        results = Results(procedure, filename)
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
