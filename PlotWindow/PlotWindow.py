from PySide6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from PySide6.QtCore import Signal

from threading import Thread, Lock
import time
from time import sleep

class PlotWindow(QtWidgets.QWidget):
    update_graph_signal = Signal()

    def createLayout(self):
        widget = QtWidgets.QWidget()
        Ver_layout = QtWidgets.QVBoxLayout()
        widget.setLayout(Ver_layout)
        


        
        Settings_group = QtWidgets.QGroupBox("Settings")
        Settings_group.setStyleSheet("QGroupBox{font: 12px;}")
        SettingsVBOX = QtWidgets.QVBoxLayout()
        Settings_group.setLayout(SettingsVBOX)
        settings_form = QtWidgets.QFormLayout()
        
        self.poll_rate = QtWidgets.QLineEdit()
        self.poll_rate.setText(str(self.rate))
        settings_form.addRow("polling rate: (s)", self.poll_rate)

        self.num_of_points_line = QtWidgets.QLineEdit()
        self.num_of_points_line.setText(str(self.num_of_points))
        settings_form.addRow("num. of points: ", self.num_of_points_line)

        SettingsVBOX.addLayout(settings_form)

        settingsBtn = QtWidgets.QPushButton("Set")
        settingsBtn.clicked.connect(self.btn_press)
        SettingsVBOX.addWidget(settingsBtn)

        clear_graph_Btn = QtWidgets.QPushButton("clear graph")
        clear_graph_Btn.clicked.connect(self.clear_graph)
        SettingsVBOX.addWidget(clear_graph_Btn)
        

        Ver_layout.addWidget(Settings_group)


        I_plot = pg.PlotWidget(axisItems = {'bottom': pg.DateAxisItem()})
        I_plot.addLegend(offset=(0,0))
        self.Icurve = I_plot.plot(pen=(0,0,0),name="I")
        Ver_layout.addWidget(I_plot)

        V_plot = pg.PlotWidget(axisItems = {'bottom': pg.DateAxisItem()})
        V_plot.setXLink(I_plot)
        V_plot.addLegend(offset=(0,0))
        self.Vcurve = V_plot.plot(pen=(0,0,0),name="V")
        Ver_layout.addWidget(V_plot)




        self.setLayout(Ver_layout)

    
    
    def __init__(self,IVGUI):
        super(PlotWindow, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.vector_lock = Lock()
        self.run = True
        self.IVGUI = IVGUI
        self.rate = 5
        self.num_of_points = 100
        self.Time = []
        self.I = []
        self.V = []
        self.createLayout()
        self.update_graph_signal.connect(self.update_graph)
        self.update_thread = Thread(target=self.update_all,daemon=True)
        self.update_thread.start()


    def btn_press(self):
        self.vector_lock.acquire()
        self.rate = float(self.poll_rate.text())
        self.num_of_points = int(self.num_of_points_line.text())
        print(self.rate)
        print(self.num_of_points)
        self.vector_lock.release()

       
    def clear_graph(self):
        self.vector_lock.acquire()
        self.Time = []
        self.I = []
        self.V = []
        self.vector_lock.release()

    def update_graph(self):
        self.vector_lock.acquire()
        try:
            self.Icurve.setData(self.Time,self.I)
            self.Vcurve.setData(self.Time,self.V)
        except Exception as e:
            print(e)
        self.vector_lock.release()



    def update_all(self):
        print("update started")
        while self.run:
            self.vector_lock.acquire()
            if len(self.Time) > self.num_of_points:
                self.Time.pop(0)
                self.I.pop(0)
                self.V.pop(0)


            now = time.time()
            self.Time.append(now)
            
            I = self.IVGUI.current
            self.I.append(I)
            
            V = self.IVGUI.voltage
        
            self.V.append(V)

            self.vector_lock.release()
            self.update_graph_signal.emit()
            sleep(self.rate)
        print("thread is closed.")


    def closeEvent(self, event):
        self.run = False
        event.accept()  # Accept the close event
