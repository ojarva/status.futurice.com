#!/usr/bin/python
#(C) 2007 Joel Kaasinen
# This code is public domain.

import sys
from numpy.core import *
from numpy.lib import *
from numpy.linalg import *


class EtaCalculator:
    """ Calculates ETA to target temperature.

        Theory of operation:
        (Tmax - T(t)) = (Tmax - T(0))*e^(-kt)
        where Tmax is the thermodynamic maximum temperature and T(t) is
        temperature as a function of time.

        Thus:

        ln (Tmax - T(t)) = ln (Tmax - T(0)) - kt  || substitute T2(t) = Tmax - T(t)
        ln T2(t) = ln T2(0) - kt

        Thus when Tmax is chosen correctly we can make a near-perfect linear fit.
    """

    def __init__(self, target, items):
        # min. temp to consider, i.e T(0)
        self.MIN = 25
        self.target = target
        self.items_raw = items
        self.items = filter(lambda x: x>self.MIN, map (float, items))
        self.timestep = 60 # seconds

    def calc(self):
        """ Calculates ETA (in seconds) to target temperature

        Returns:
            Seconds before reaching target temperature

        """
        kbest = None
        Tmaxbest = None
        resids = None
        T = map( lambda x: [x, 1], range(len(self.items))) # t vector for fit

        for Tmax in range(100,500,5): # step thru temps
            y = map( lambda x: log(Tmax - x), self.items ) # T2(t) vector
            # solve least squares for Tk=y
            k,r,rank,s = lstsq(T, y)
    
            if resids == None or r < resids: # we've got a better fit
                kbest = k
                resids = r
                Tmaxbest = Tmax

        t0 = roots([k[0], k[1]-log(Tmax-self.target)])[0]-(len(T))
        return t0 * self.timestep

def main(args):
    target = float(args[1])
    etacalculator = EtaCalculator(target, args[2:])
    print etacalculator.calc()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
