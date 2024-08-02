from enum import Enum
import socket
from select import select
from time import sleep
from PySide6.QtCore import Signal,QObject,Slot

class SES_API(QObject):
    class ConnectionStatus(Enum):
        Error = 0
        Listening = 1
        Connected = 2

    Stop = Signal()
    ConnectionStatusChanged = Signal(object)


    def __init__(self,setCurrent,getCurrent):
        super(SES_API, self).__init__()
        self.HOST = "127.0.0.1"
        self.PORT = 5012  # Port to listen on (non-privileged ports are > 1023)
        self.run = True
        self.conn = None
        self.listening = False
        self.connected = False
        self.setCurrent = setCurrent
        self.getCurrent = getCurrent


    def get_Curr(self):
        #Not to be confused with getCurrent (confusing? YES!)
        print("Get me curr!")
        print(self.getCurrent())
        self.conn.send("{}\n".format(self.getCurrent()).encode())


    def set_Curr(self,data):
        print("SetCurr")
        print(float(data.replace("Curr","")))
        self.setCurrent(float(data.replace("Curr","")))

    def stop(self):
        self.setCurrent(0.0)


    def handle_connection(self):#this is main loop.
        #GUI: not connected
        self.ConnectionStatusChanged.emit(self.ConnectionStatus.Error)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setblocking(True)
            s.settimeout(0.01)
            s.bind((self.HOST, self.PORT))
            s.listen()

            while self.run:
                print("listening")
                self.listening = True
                self.ConnectionStatusChanged.emit(self.ConnectionStatus.Listening)

                read,write,_ = select([s],[s],[],0.01)
                while(not read):
                    #waiting for connection without blocking
                    #This works good
                    read, write, _ = select([s], [s], [],0)
                    sleep(0.1)

                self.conn, addr = s.accept()
                self.conn.settimeout(0.1)
                with self.conn:
                    self.ConnectionStatusChanged.emit(self.ConnectionStatus.Connected)
                    self.listening = False
                    self.connected = True
                    print("Connected by {}".format(addr))

                    while self.connected and self.run:
                        #we are stuck here!
                        try:
                            data = self.conn.recv(512)
                        except socket.timeout as e:
                            #print(e)
                            #print("non blocking")
                            sleep(0.1)
                            continue

                        if data == b'':
                            sleep(0.01)
                            continue

                        for data in data.decode("UTF-8").split('\n'):
                            print(data)
                            if("?" in data):
                                self.get_Curr() #Handle data request
                            elif "Curr" in data: #Curr0.1 for example
                                self.set_Curr(data) #handle set curr request
                            elif "STOP" in data:
                                self.stop()
                            else:
                                if data!=r"\n":
                                    #print(data) # anything else please?
                                    pass

                            if data=="exit":
                                # closing connection, but awaiting another one...
                                self.connected = False
                                break

                        sleep(0.01)


                sleep(0.1)
                
    @Slot()
    def closeLoop(self):
        print("closing SES loop.")
        self.run = False