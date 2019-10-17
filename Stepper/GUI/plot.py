import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style,use
use('WXagg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from wx import ID_ANY
import timeit


class Plotter(FigureCanvasWxAgg):
    
    def __init__(self,parent, get_reading):
        self.fig = plt.figure()
        super().__init__(parent,id=ID_ANY,figure=self.fig)
        self.ax1 = self.fig.add_subplot(1,1,1)
        self.get_reading = get_reading
        plt.ion()
        self.xs = []
        self.ysf = []
        
    def set_start(self, start):
        self.start = start
    def update(self,e):
        
    
       
        self.xs.append(int(timeit.default_timer())-self.start)
        self.ysf.append(float(self.get_reading()))
                    
        
        if len(self.ysf) > 1000:
            for list in self.ysf, self.xs:
                list.pop(0)
        self.ax1.clear()
        self.ax1.plot(self.xs, self.ysf)
        self.draw()
    def clear(self):
        self.xs, self.ysf = [],[]