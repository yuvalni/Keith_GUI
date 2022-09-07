import socket
from select import select
from time import sleep


class SES_API:
    def __init__(self,setCurrent,getCurrent):
        self.HOST = "127.0.0.1"
        self.PORT = 5011  # Port to listen on (non-privileged ports are > 1023)
        self.conn = None
        self.listening = False
        self.connected = False
        self.setCurrent = setCurrent
        self.getCurrent = getCurrent


    def get_Curr():
        self.conn.send("{}\n".format(self.get_Curr()).encode())


    def set_Curr(data):
        self.setCurrent(float(data.replace("Curr","")))

    def stop():
        self.setCurrent(0.0)

    def handle_connection(self):#this is main loop.
        #GUI: not connected
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setblocking(True)
            s.settimeout(0.01)
            s.bind((self.HOST, self.PORT))
            s.listen()

            while True:
                print("listening")
                self.listening = True
                #gui: listening ...yellow
                eel.set_socket_value(1)
                read,write,_ = select([s],[s],[],0.01)
                while(not read):
                    #waiting for connection without blocking
                    #This works good
                    read, write, _ = select([s], [s], [],0)
                    sleep(0.1)

                self.conn, addr = s.accept()
                self.conn.settimeout(0.1)
                with self.conn:
                    #GUI: Connected! green!
                    self.listening = False
                    self.connected = True
                    print("Connected by {}".format(addr))

                    while self.connected:
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
                            if("?" in data):
                                self.get_Curr() #Handle data request
                            elif "CURR" in data: #MOVX5.0 for example
                                self.set_Curr(data) #handle move request
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
