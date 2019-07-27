#Author-Kyle Diaz
#Description-Creates a sprocket from given parameters

import adsk.core, adsk.fusion, adsk.cam, traceback
import math

class Sprocket:
    # the names used in here follow the convention used in  "Chains for Power Transmission
    # and Material Handling handbook", which is considered the industry standard
    def __init__(self, chain_pitch, number_of_teeth, roller_diameter):
        self.P = chain_pitch
        self.N = number_of_teeth
        self.Dr = roller_diameter
    
    # most functions were copied verbatim, but for some, I was able to simplify
    # them using the other functions    
    def Ds(self):
        return 1.0005 * self.Dr + 0.003
    def R(self):
        return self.Ds / 2
    def A(self):
        return 35 + 60 / self.N
    def B(self):
        return 18 - 56 / self.N
    def ac(self):
        return 0.8 * self.Dr
    def M(self):
        return self.ac * math.cos(self.A)
    def T(self):
        return self.ac * math.sin(self.A)
    def E(self):
        return 1.3025 * self.Dr + 0.0015
    def yz(self):
        return self.Dr * (1.4 * math.sin(17 - 64 / self.N) - self.B)
    def ab(self):
        return 1.4 * self.Dr
    def W(self):
        return 1.4 * self.Dr * math.cos(180 / self.N)
    def V(self):
        return 1.4 * self.Dr * math.sin(180 / self.N)
    def F(self):
        return self.Dr * (0.8 * math.cos(self.B) + 1.4 * math.cos(17 - 64 / self.N) - 1.3025) - .0015
    def H(self):
        return math.sqrt(self.F ** 2 - (1.4 * self.Dr - self.P / 2) ** 2)
    def S(self):
        return self.P / 2 * math.cos(180 / self.N) + self.H * math.sin(180 / self.N)
    def PD(self):
        return self.P / math.sin(180 / self.N)
  

class SprocketComponent(Sprocket):
    def __init__(self, chain_pitch, number_of_teeth, roller_diameter):
        super.__init__(chain_pitch, number_of_teeth, roller_diameter)
    def build_sprocket(self):
        pass


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        ui.messageBox('Hello script')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
