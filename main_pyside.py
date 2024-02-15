
from pymeasure.instruments.keithley import Keithley2400
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt,QTimer
from SES_Interface import SES_API
import threading
import time
import sys
from simple_pid import PID
from random import random
#:VOLTage:PROTection:TRIPped? (for source)



class KeithleyGUI(QtWidgets.QWidget,):

    def __init__(self,*args, **kwargs):
        super(KeithleyGUI, self).__init__(*args, **kwargs)
        self.initLayout()
        self.keithley = None
        try:
            self.keithley = Keithley2400("GPIB::16")
            pass
        except:
            print("no keithley")
            self.keithley = None

        self.output = False
        self.current = 0.0
        self.voltage=0.0
        self.resistance = 0.0
        self.nplc = 2
        self.Vcomp = 2.0 #source compliance
        self.VMlimit = 1.0 #measure limit!
        self.Vrange = 1.0
        self.rear_terminals = True
        self.pid_start_current = 0

        self.initKeithley()
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateValues)
        self.updateTimer.start(100)
        #self.SES_API = SES_API(self.setCurrent,self.getCurrent)
        #self.API_thread = threading.Thread(target=self.SES_API.handle_connection,daemon=True)
        #self.API_thread.start()

        self.pid = PID(1.0, 0.0, 0.0, setpoint=0.0) # initial parameters
        self.pid.sample_time = 0.01  # Update every 0.01 seconds
        self.pid.output_limits = (-100, 20) #in mA
        self.PID_timer =QTimer()
        self.PID_timer.timeout.connect(self.run_PID)
        self.PID_timer.setInterval(10) #update every 10 millisec


    def initLayout(self):
        layout = QtWidgets.QVBoxLayout()
        Current_group = QtWidgets.QGroupBox("Set current")
        Current_group.setStyleSheet("QGroupBox{font: 12px;}")
        vbox = QtWidgets.QVBoxLayout()
        Current_group.setLayout(vbox)
        layout.addWidget(Current_group)

        double_validator = QtGui.QDoubleValidator()

        Cuurent_form = QtWidgets.QFormLayout()
        self.setCurrentValue = QtWidgets.QLineEdit()
        self.setCurrentValue.setValidator(double_validator)
        self.setCurrentValue.setText("0.0")
        Cuurent_form.addRow("Set Current", self.setCurrentValue)
        vbox.addLayout(Cuurent_form)

        PID_voltage_Form = QtWidgets.QFormLayout()
        self.PID_voltage_target = QtWidgets.QLineEdit()
        self.PID_voltage_target.setValidator(double_validator)
        self.PID_voltage_target.setText("")
        self.PID_voltage_target.setEnabled(False)
        PID_voltage_Form.addRow("PID target", self.PID_voltage_target)
        vbox.addLayout(PID_voltage_Form)

        setCurrBtn = QtWidgets.QPushButton("Set current [mA]")
        setCurrBtn.clicked.connect(lambda: self.setCurrent(float(self.setCurrentValue.text())))
        vbox.addWidget(setCurrBtn)


        applyForm = QtWidgets.QFormLayout()
        self.applyCurrentCB = QtWidgets.QCheckBox()
        self.applyCurrentCB.stateChanged.connect(lambda: self.toggleOutput(self.applyCurrentCB.checkState()))
        applyForm.addRow("Apply Current",self.applyCurrentCB)

        self.runPIDCB = QtWidgets.QCheckBox()
        self.runPIDCB.stateChanged.connect(lambda: self.handle_PID_CB_change(self.runPIDCB.checkState()))
        applyForm.addRow("Start PID",self.runPIDCB)

        vbox.addLayout(applyForm)


        Col2 = QtWidgets.QVBoxLayout()
        layout.addLayout(Col2)


        settingsGroup = QtWidgets.QGroupBox("Keithley Settings")
        settingsGroup.setStyleSheet("QGroupBox{font: 12px;}")
        settingsGroupVbox = QtWidgets.QVBoxLayout()
        settingsGroup.setLayout(settingsGroupVbox)
        Col2.addWidget(settingsGroup)

        settingsForm = QtWidgets.QFormLayout()
        self.rear_terminalsCB = QtWidgets.QCheckBox()
        self.rear_terminalsCB.setChecked(True)
        self.rear_terminalsCB.stateChanged.connect(lambda: self.changeTerminals(self.rear_terminalsCB.checkState()))
        settingsForm.addRow("use rear terminals",self.rear_terminalsCB)
        ### voltage comp setting
        VcomRow = QtWidgets.QHBoxLayout()
        VcomRow.addWidget(QtWidgets.QLabel("V compliance"))
        self.VcomplianceValue = QtWidgets.QLineEdit()
        self.VcomplianceValue.setValidator(double_validator)
        self.VcomplianceValue.setText("4.0")
        VcomRow.addWidget(self.VcomplianceValue)

        settingsGroupVbox.addLayout(settingsForm)
        SetVcompBtn = QtWidgets.QPushButton("Set compliance")
        SetVcompBtn.clicked.connect(lambda: self.setSourceVoltageCompliance(float(self.VcomplianceValue.text())))
        VcomRow.addWidget(SetVcompBtn)
        settingsGroupVbox.addLayout(VcomRow)
        ### voltage comp setting end

        ### voltage nplc setting
        nplcRow = QtWidgets.QHBoxLayout()
        nplcRow.addWidget(QtWidgets.QLabel("nplc"))
        self.nplcValue = QtWidgets.QLineEdit()
        self.nplcValue.setValidator(double_validator)
        self.nplcValue.setText("1.0")
        nplcRow.addWidget(self.nplcValue)
        SetNplcBtn = QtWidgets.QPushButton("Set nplc")
        SetNplcBtn.clicked.connect(lambda: self.SetVoltageNPLC(float(self.nplcValue.text())))
        nplcRow.addWidget(SetNplcBtn)
        settingsGroupVbox.addLayout(nplcRow)
        ### voltage nplc setting end

        ### voltage range setting start
        VrangeRow = QtWidgets.QHBoxLayout()
        VrangeRow.addWidget(QtWidgets.QLabel("Voltage range"))
        self.VoltageRangeValue = QtWidgets.QLineEdit()
        self.VoltageRangeValue.setValidator(double_validator)
        self.VoltageRangeValue.setText("1.0")
        VrangeRow.addWidget(self.VoltageRangeValue)
        SetVRangecBtn = QtWidgets.QPushButton("Set Vrange")
        SetVRangecBtn.clicked.connect(lambda: self.SetVoltageRange(float(self.VoltageRangeValue.text())))
        VrangeRow.addWidget(SetVRangecBtn)
        settingsGroupVbox.addLayout(VrangeRow)
        ### voltage range setting end

        ###PID settings
        PIDRow = QtWidgets.QHBoxLayout()
        PIDRow.addWidget(QtWidgets.QLabel("P"))
        self.pid_P_value = QtWidgets.QLineEdit()
        self.pid_P_value.setValidator(double_validator)
        self.pid_P_value.setText("1.0")
        PIDRow.addWidget(self.pid_P_value)

        PIDRow.addWidget(QtWidgets.QLabel("I"))
        self.pid_I_value = QtWidgets.QLineEdit()
        self.pid_I_value.setValidator(double_validator)
        self.pid_I_value.setText("0.0")
        PIDRow.addWidget(self.pid_I_value)

        PIDRow.addWidget(QtWidgets.QLabel("D"))
        self.pid_D_value = QtWidgets.QLineEdit()
        self.pid_D_value.setValidator(double_validator)
        self.pid_D_value.setText("0.0")
        PIDRow.addWidget(self.pid_D_value)

        settingsGroupVbox.addLayout(PIDRow)
        ###PID settings end


        measureGroup = QtWidgets.QGroupBox("Measured Values")
        measureGroup.setStyleSheet("QGroupBox{font: 12px;}")
        measureGroupVbox = QtWidgets.QVBoxLayout()
        measureGroup.setLayout(measureGroupVbox)

        measure_form = QtWidgets.QFormLayout()
        self.CurrentValue = QtWidgets.QLineEdit()
        self.CurrentValue.setEnabled(False)
        measure_form.addRow("Current:", self.CurrentValue)

        self.VoltageValue = QtWidgets.QLineEdit()
        self.VoltageValue.setEnabled(False)
        measure_form.addRow("Voltage:", self.VoltageValue)

        self.ResistanceValue = QtWidgets.QLineEdit()
        self.ResistanceValue.setEnabled(False)
        measure_form.addRow("Resistance:", self.ResistanceValue)
        measureGroupVbox.addLayout(measure_form)
        Col2.addWidget(measureGroup)

        self.setLayout(layout)

    def initKeithley(self):
        if self.keithley:
            self.keithley.reset()
            # setting current params
            #self.keithley.use_front_terminals()
            self.keithley.use_rear_terminals()
            self.keithley.apply_current(None, self.Vcomp)
            self.keithley.wires = 4  # set to 4 wires

            self.keithley.source_current = 0
            self.keithley.auto_zero = True

            self.keithley.measure_voltage(self.nplc, self.VMlimit, True)

            #just for fun:
            #self.keithley.beep(400, 0.5)
            #self.keithley.beep(600, 0.5)
            self.keithley.triad(400,0.3)
            self.keithley.write(":SYST:BEEP:STAT OFF")
            print("Keithley ready.")

    def setSourceVoltageCompliance(self,V):
        self.Vcomp = V
        if self.keithley:
            self.keithley.apply_current(self.current, self.Vcomp)
        else:
            print("No keithley Vcomp = {}".format(V))

    def SetVoltageNPLC(self,nplc):
        self.nplc = nplc
        if self.keithley:
            self.keithley.voltage_nplc = self.nplc
        else:
            print("No keithley nplc = {}".format(nplc))

    def SetVoltageRange(self,Vrange):
        self.Vrange = Vrange
        if self.keithley:
            self.keithley.voltage_range = self.Vrange
        else:
            print("No keithley Vrange = {}".format(Vrange))
    def changeTerminals(self,state):
        if state == Qt.CheckState.Checked:
            self.rear_terminals = True
        else:
            self.rear_terminals = False
        if self.keithley:
            if self.rear_terminals:
                self.keithley.use_rear_terminals()
            else:
                self.keithley.use_front_terminals()
        else:
            print("no keithley. rear terminals? {}: ".format(self.rear_terminals))

    def setMeasureVoltageLimit(self):
        self.keithley.measure_voltage(2, self.VMlimit, False)

    def getCurrent(self):
        #helper function for SES API
        return self.current

    def setCurrent(self,I):
        if self.keithley:
            assert I < 90
            self.keithley.source_current = I/1000 #I in mA, keithley recieve Amps
        else:
            print("no keithley. I={}mA".format(I))
        self.current = I

    def toggleOutput(self,state):
        if state == Qt.CheckState.Checked:
            self.output = True
        else:
            self.output = False
        if self.keithley:
            if self.output:
                self.keithley.enable_source()
            else:
                self.keithley.disable_source()
        else:
            print("no keithley, output: {}".format(self.output))

    def updateValues(self):
        if not self.output:
            return True

        if self.keithley:
            #self.actualCurrent = self.keithley.current*1000 #kiethly talk in amps, we want mA

            self.voltage = self.keithley.voltage*1000 #keithley talks in Volts, we want mV
            if self.current > 0 :
                self.resistance = self.voltage/self.current
            else:
                self.resistance = 0.0
        else:
            self.actualCurrent = 999

        self.CurrentValue.setText(str(self.current))
        self.VoltageValue.setText(str(self.voltage))
        self.ResistanceValue.setText(str(self.resistance))


    def handle_PID_CB_change(self,state):
        if state != Qt.CheckState.Checked:
            self.stop_PID()
        if state == Qt.CheckState.Checked:
            self.start_PID()

    def start_PID(self):
        P = float(self.pid_P_value.text())
        I = float(self.pid_I_value.text())
        D = float(self.pid_D_value.text())
        print(P,I,D)
        self.pid.tunings = (P, I, D)
        self.toggleOutput(Qt.CheckState.Checked) #start current
        time.sleep(0.05) #wait 50 ms
        if self.keithley:
            self.voltage = self.keithley.voltage*1000 #keithley talks in Volts, we want mV
        else:
            self.voltage = 0.05
        self.pid_start_current = float(self.setCurrentValue.text())
        self.pid.setpoint = self.voltage
        #self.pid.setpoint = float(self.PID_voltage_target.text())
        self.PID_voltage_target.setText(str(self.pid.setpoint))
        self.setCurrentValue.setEnabled(False) # I controll the current now
        self.applyCurrentCB.setEnabled(False)
        self.PID_timer.start()

    def stop_PID(self):
        self.toggleOutput(Qt.CheckState.Unchecked) #start current
        self.PID_timer.stop()
        self.setCurrentValue.setEnabled(True) # I controll the current now
        self.applyCurrentCB.setEnabled(True)

    def run_PID(self):
        if self.keithley:
            self.voltage = self.keithley.voltage*1000 #keithley talks in Volts, we want mV
        else:
            self.voltage = self.pid.setpoint*random()

        self.VoltageValue.setText(str(self.voltage))
        output = self.pid(self.voltage)

        assert self.pid_start_current + output < 80.0 #don't put too much current!!
        self.current = self.pid_start_current + output
        if self.current < 80.0:
            self.setCurrent(self.current) #this function expects to get in milliamps
            self.CurrentValue.setText(str(self.current)) #show the current





if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    GUI = KeithleyGUI()
    GUI.show()
    app.exec()
