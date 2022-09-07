import imgui
import glfw
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer
from pymeasure.instruments.keithley import Keithley2400
import time

def impl_glfw_init(window_name="minimal ImGui/GLFW3 example", width=1280, height=720):
    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(int(width), int(height), window_name, None, None)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window


class GUI(object):

    def __init__(self):
        super().__init__()
        self.backgroundColor = (0, 0, 0, 0.5)
        self.window = impl_glfw_init(width=700, height=500)
        gl.glClearColor(*self.backgroundColor)
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)

        try:
            self.keithley = Keithley2400("GPIB::16")
        except:
            print("no keithley")
            self.keithley = False

        self.output = False
        self.current = 0.0
        self.voltage=0.0
        self.Vcomp = 2.0 #source compliance
        self.VMlimit = 2.0 #measure limit!
        self.initKeithley()
        self.loop()

    def initKeithley(self):
        if self.keithley:
            self.keithley.reset()
            # setting current params
            self.keithley.use_front_terminals()
            self.keithley.apply_current(0.01, self.Vcomp)
            self.keithley.wires = 4  # set to 4 wires
            # self.keithley.compliance_voltage = V_comp
            self.keithley.source_current = 0

            # setting voltage read params
            self.keithley.measure_voltage(1, self.VMlimit, False)
            #just for fun:
            self.keithley.beep(400, 0.5)
            self.keithley.beep(600, 0.5)
            self.keithley.write(":SYST:BEEP:STAT OFF")

    def setSourceVoltageCompliance(self):
        self.keithley.apply_current(0.01, self.Vcomp)

    def setMeasureVoltageLimit(self):
        self.keithley.measure_voltage(1, self.VMlimit, False)

    def loop(self):
        voltage_check_time = time.time()
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.impl.process_inputs()
            imgui.new_frame()
            imgui.begin("Keithley GUI", True)


            imgui.text("Current control")

            changed, self.current = imgui.input_double('Applied current [mA]', self.current)
            if changed:                
                self.keithley.source_current = self.current/1000
                assert self.keithley.source_current < 0.01
                # need to do something more gentle
            _, self.output = imgui.checkbox("Apply current", self.output)
            if _:
                if self.output:
                    self.keithley.enable_source()
                else:
                    self.keithley.disable_source()


            if (time.time() - voltage_check_time) > 0.3:
                if self.output:
                    self.voltage = self.keithley.voltage #in Volts
                else:
                    self.voltage = 0
                voltage_check_time = time.time()

            imgui.separator()
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            imgui.begin_group()

            _,_ = imgui.input_double('Voltage [mv]', self.voltage*1000 ,imgui.INPUT_TEXT_READ_ONLY)


            if self.current == 0:
                _, _ = imgui.input_double('Resistance [Ohm]', 0.0, imgui.INPUT_TEXT_READ_ONLY)
            else:
                _, _ = imgui.input_double('Resistance [Ohm]', self.voltage / (self.current / 1000), imgui.INPUT_TEXT_READ_ONLY)
            imgui.end_group()
            imgui.separator()
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            changed, self.Vcomp = imgui.input_double('source voltage compliance[V]', self.Vcomp)
            if changed:
                self.setSourceVoltageCompliance()

            imgui.end()

            imgui.render()

            gl.glClearColor(*self.backgroundColor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)

        self.impl.shutdown()
        glfw.terminate()


if __name__ == "__main__":
    gui = GUI()
