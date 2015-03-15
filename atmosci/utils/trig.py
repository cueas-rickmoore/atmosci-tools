""" Trigonometric functions that handle degrees rather than radians
"""
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DegreeTrigonometry(object):

    def __init__(self, trig_module):
        self.trig = trig_module

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # standard trigonometry functions
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def acos(self, cosine):
        return self.degrees(self.trig.acos(cosine))

    def asin(self, sine):
        return self.degrees(self.trig.asin(sine))

    def atan(self, tangent):
        return self.degrees(self.trig.atan(tangent))

    def cos(self, degrees):
        return self.trig.cos(self.radians(degrees))

    def sin(self, degrees):
        return self.trig.sin(self.radians(degrees))

    def tan(self, degrees):
        return self.trig.tan(self.radians(degrees))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # hyperbolic trigonometry functions
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def acosh(self, cosine):
        return self.degrees(self.trig.acosh(cosine))

    def asinh(self, sine):
        return self.degrees(self.trig.asinh(sine))

    def atanh(self, tangent):
        return self.degrees(self.trig.atanh(tangent))

    def cosh(self, degrees):
        return self.trig.cosh(self.radians(degrees))

    def sinh(self, degrees):
        return self.trig.sinh(self.radians(degrees))

    def tanh(self, degrees):
        return self.trig.tanh(self.radians(degrees))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # radians/degrees conversion
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def degrees(self, radians):
        return self.trig.degrees(radians)

    def radians(self, degrees):
        return self.trig.radians(degrees)

