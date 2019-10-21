import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style,use
use('WXagg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from wx import ID_ANY
import timeit
import time

from threading import Lock
class Plotter(FigureCanvasWxAgg):
    
    def __init__(self,parent, get_reading,exp_str):
        self.fig = plt.figure()
        super().__init__(parent,id=ID_ANY,figure=self.fig)
        self.ax1 = self.fig.add_subplot(1,1,1)
        self.get_reading = get_reading
        plt.ion()
        self.xs = []
        self.ysf = []
        self.file = open("Stepper/exp_data/{}.txt".format(exp_str()),"w+")
        self.reading = False
        
    def set_start(self, start):
        self.start = start
    def read(self,start_time):
        while self.reading:
            now = time.time()
            self.file.write(str(now-start_time)+"; "+str(self.get_reading())+"\n")

            time.sleep(0.01)
        
        
    def update(self,e):
        self.file.seek(0)
        lines = self.file.readlines()
        
        for line in lines:
            time, force = line.replace("\n", "").split("; ")
            self.xs.append(float(time))
            self.ysf.append(float(force))
        if len(self.xs) > 500:
            self.xs , self.ysf = self.xs[-500::], self.ysf[-500::]
        
        
        self.ax1.clear()
        self.ax1.plot(self.xs,self.ysf)
    def clear(self):
        self.ax1.clear()
        self.xs, self.ysf = [], []
        self.file.seek(0)
        self.file.truncate()