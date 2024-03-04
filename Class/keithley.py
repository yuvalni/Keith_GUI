import random
from time import sleep
import pyvisa


class MockUp():
    def __init__(self):
        pass
    
    def connect(self):
        return True
    
    def disconnect(self):
        return True
    
    def measure_Pulse(self,I):
        sleep(1000/1000)
        return ([0.0,0.001,0.0025,0.004],[0.0,I,I,0])
    
    def measure_script(self,I,AVGnum):
       return (25+random.random())
    


class Keithley2600():
    def __init__(self):
        #self.address = 'USB0::0x05E6::0x2614::4083836::INSTR'
        self.address = 'GPIB0::26::INSTR'
        self.keithley = None
        self.connected = False
        
    
    def connect(self):
        rm = pyvisa.ResourceManager()
        self.keithley = rm.open_resource(self.address)
        self.connected = True
        self.keithley.clear()
        #self.keithley.clear_queue()
        return True
    
    def disconnect(self):
        self.keithley.close()
        self.IsConnected=False
        return True
    
    def write(self,st):
        self.keithley.write(st)

    def read(self):
        return self.keithley.read()

    def load_script(self,script_name, script_text, num_of_points, script_buffer, delay_time):
        self.script_name = script_name
        self.script_text = script_text
        self.script_delay_time = int(delay_time)
        self.script_num_of_points = int(num_of_points)
        self.script_buffer = int(script_buffer)

        full_script = "loadscript {0}\r\n{1}\r\nendscript".format(self.script_name, self.script_text)
        row_split = full_script.split('\n');
        i = 0;
        while row_split[i] != "endscript":
            self.write(row_split[i])
            #print(row_split[i])
            i = i + 1

        self.write(row_split[i])
        #print(row_split[i])
        self.write("{0}.save()".format(self.script_name))
        return "{0} was Loaded".format(self.script_name)
    

    def call_script(self,script_name):
        self.write("{0}.run()".format(script_name))
        return "{0} is running".format(script_name)
    

    def read_data(self):
        self.data = []
        for i in range(self.script_num_of_points):
            out = self.keithley._read_raw(size=self.script_buffer * 32)
            sout = out.decode().replace('\n', '').split(',')
            fout = list()
            for istr in sout:
                fout.append(float(istr))
            self.data.append(fout)
        return self.data
    

    def measure(self,script_name):
        self.call_script(script_name)
        sleep(self.script_delay_time)
        return self.read_data()
        

    def apply_current(self,current_range=None,compliance_voltage=0.1):
      self.write("smua.source.func = smua.OUTPUT_DCAMPS")
      if current_range:
           self.write("smua.source.rangei = {0}".format(current_range))
      else:
           self.write("smua.source.autorangei = smua.AUTORANGE_ON")
      self.write("smua.source.limitv = {0}".format(compliance_voltage))
      
      
      
    def apply_voltage(self,voltage_range=None,compliance_current=0.1):
        self.write("smua.source.func = mua.OUTPUT_DCVOTLS")
        if voltage_range:
            self.write("smua.source.rangev = {0}".format(voltage_range))
        else:
            self.write("smua.source.autorangev = smua.AUTORANGE_ON")
        self.write("smua.source.limiti = {0}".format(compliance_current))

    def measure_current(self,nplc=1,current=0.00001,auto_range=True):
        self.write("smua.measure.nplc = {0}".format(nplc))
        if auto_range:
            self.write("smua.measure.autorangei = smua.AUTORANGE_ON")
        else:
            self.write("smua.measure.autorangei = smua.AUTORANGE_OFF")
        self.set_current(current)
        
    def measure_voltage(self,nplc=1,auto_range=True):
        self.write("smua.measure.nplc = {0}".format(nplc))
        if auto_range:
            self.write("smua.measure.autorangev = smua.AUTORANGE_ON")
        else:
            self.write("smua.measure.autorangev = smua.AUTORANGE_OFF") 
        
            
    def set_current(self,I):
        self.write("smua.source.leveli = {0}".format(I))
        
    def set_voltage(self,V):
        self.write("smua.source.levelv = {0}".format(V))
        
    def set_current_range(self,current_range):
        self.write("smua.measure.rangei = {0}".format(current_range))

        
    def set_voltage_range(self,voltage_range):
        self.write("smua.measure.rangev = {0}".format(voltage_range))
        

        
    def set_nplc(self,nplc):
        self.write("smua.measure.nplc = {0}".format(nplc))
        
    def set_voltage_compliance(self,limit_v):
        self.write("smua.source.limitv = {0}".format(limit_v))
        
    def set_current_compliance(self,limit_i):
        self.write("smua.source.limiti = {0}".format(limit_i))
        
    def enable_source(self):
        self.write("smua.source.output = smua.OUTPUT_ON")
        
    def disable_source(self):
        self.write("smua.source.output = smua.OUTPUT_OFF")
    
    def get_voltage(self):
        self.write("print(smua.measure.v())")
        sleep(0.001)
        return self.read()
    
    def get_current(self):
        self.write("print(smua.measure.i())")
        sleep(0.001)
        return self.read()
    
    def set_4wires(self,wires4=True):
        if wires4:
            self.write("smua.sense = smua.SENSE_REMOTE")
        else:
            self.write("smua.sense = smua.SENSE_LOCAL")

    def disable_beep(self):
        self.write("beeper.enable = beeper.OFF")



    def measure_script(self,meas_curr,AVGnum):
        self.keithley.clear()
        with open(r".\keithley\measure_script.txt") as f:
            script_txt = f.read()
        script_txt = script_txt.replace("{meas_curr}",str(meas_curr))
        script_txt  = script_txt.replace("{AVGnum}",str(int(AVGnum)))
        
        self.load_script("measure",script_txt,5,50,2)
        #print(self.measure("measure"))
        Ip,Vp,Im,Vm,R = self.measure("measure")
        return R


    def pulse_script(self,pulseMax,pulseMin,nplc,tbm,V_comp):
        self.keithley.clear()
        with open(r".\keithley\pulse_script.txt") as f:
        #with open(r".\keithley\pulse_script2.txt") as f:
            script_txt = f.read()
        print(pulseMax)
        script_txt = script_txt.replace("{pulseMax}",str(pulseMax))
        script_txt = script_txt.replace("{pulseMin}",str(pulseMin))
        script_txt = script_txt.replace("{nplc}",str(nplc))
        script_txt = script_txt.replace("{tbm}",str(tbm))
        script_txt = script_txt.replace("{V_comp}",str(V_comp))
        self.load_script("pulse",script_txt, num_of_points=3, script_buffer=10000, delay_time=2)
        #self.load_script("pulse2",script_txt, num_of_points=2, script_buffer=10000, delay_time=2)


        #t,I = self.measure("pulse2")
        V,I,t = self.measure("pulse")
        
        return t,I


    def clear_queue(self):
        #TODO tie this to file option
        self.keithley.clear()
        #self.keithley.clear_queue()