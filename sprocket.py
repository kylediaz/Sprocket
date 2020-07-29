class Sprocket:

    # the names used in here follow the convention used in  "Chains for Power Transmission
    # and Material Handling handbook", which is considered the industry standard
    def __init__(self, chain_pitch, number_of_teeth, roller_diameter):
        self.P = float(chain_pitch)
        self.N = float(number_of_teeth)
        self.Dr = float(roller_diameter)

    # most functions were copied verbatim, but for some, I was able to simplify
    # them using the other functions

    @property
    def Ds(self):
        return 1.0005 * self.Dr + 0.003

    @property
    def R(self):
        return self.Ds / 2

    @property
    def A(self):
        return 35 + 60 / self.N

    @property
    def B(self):
        return 18 - 56 / self.N

    @property
    def ac(self):
        return 0.8 * self.Dr

    @property
    def M(self):
        return self.ac * math.cos(math.radians(self.A))

    @property
    def T(self):
        return self.ac * math.sin(math.radians(self.A))

    @property
    def E(self):
        return 1.3025 * self.Dr + 0.0015

    @property
    def yz(self):
        return self.Dr * (1.4 * math.sin(math.radians(17 - 64 / self.N)) - self.B)

    @property
    def ab(self):
        return 1.4 * self.Dr

    @property
    def W(self):
        return 1.4 * self.Dr * math.cos(math.radians(180 / self.N))

    @property
    def V(self):
        return 1.4 * self.Dr * math.sin(math.radians(180 / self.N))

    @property
    def F(self):
        return self.Dr * (0.8 * math.cos(math.radians(self.B)) + 1.4 * math.cos(math.radians(17 - 64 / self.N)) - 1.3025) - .0015

    @property
    def H(self):
        return math.sqrt(self.F ** 2 - (1.4 * self.Dr - self.P / 2) ** 2)

    @property
    def S(self):
        return self.P / 2 * math.cos(math.radians(180 / self.N)) + self.H * math.sin(math.radians(180 / self.N))

    @property
    def PD(self):
        return self.P / math.sin(math.radians(180 / self.N))
