
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('WXagg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from collections import deque
from wx import ID_ANY
import numpy as np
import timeit
import time
import threading

#Lock object for locking the read thread
lock = threading.RLock()

class Plotter(FigureCanvasWxAgg):
    def __init__(self,parent, pos_q,force_q,control_q, max_len=10000,plot_delay=0.3, read_delay=0.0001):
        self.fig = plt.figure(figsize=(7, 6), dpi=75)
        self.parent = parent
        super().__init__(self.parent,id=ID_ANY,figure=self.fig)
        self.force = self.fig.add_subplot(211)
        self.position = self.fig.add_subplot(212)
        self.force.title.set_text('Force')
        self.position.title.set_text('Position')
        self.max_len=max_len

        self.plot_delay = plot_delay
        self.read_delay = read_delay

        self.force_q = force_q
        self.pos_q = pos_q
        self.control_q = control_q


        self.timer =None


        self.force_over_time = deque()
        self.position_over_time = deque()
        self.times = deque()

        plt.ion()
        self.reading = False


    def read_data(self, ps):
        global lock

        self.reading = True
        while self.reading:
            ctrl = self.control_q.get()

            if ctrl == 'KILL':
                ps.put(ctrl)
                break

            else:
                self.control_q.put(False)

            ps.put(False)
            lock.acquire()

            if self.timer is None:
                self.timer = timeit.default_timer()
            try:
                force, pos = self.force_q.get(), self.pos_q.get()
                self.force_over_time.append(force)
                self.position_over_time.append(pos)
                self.times.append(timeit.default_timer()-self.timer)


                if len(self.position_over_time) >self.max_len:
                    self.position_over_time.popleft()
                    self.force_over_time.popleft()
                    self.times.popleft()
            finally:
                lock.release()



    def plotting(self,plot_stop_q):

        force_line = self.force.plot(self.times,self.force_over_time,'r')
        position_line = self.position.plot(self.times,self.position_over_time,'b')
        self.plot_stop_q = plot_stop_q

        self.read_thread = threading.Thread(target=self.read_data,args= (self.plot_stop_q,),daemon=True)
        self.read_thread.start()
        time.sleep(self.plot_delay)

        while True:
            if plot_stop_q.get() == 'KILL':
                self.reading = False
                self.read_thread.join()
                break
            else:
                plot_stop_q.put(False)

            if self.reading:
                force_line[0].set_xdata(self.times)
                force_line[0].set_ydata(self.force_over_time)
                position_line[0].set_xdata(self.times)
                position_line[0].set_ydata(self.position_over_time)


            self.fig.canvas.draw()

            self.force.set_xlim(np.min(self.times), np.max(self.times) * 1.05)
            self.position.set_xlim(np.min(self.times), np.max(self.times)* 1.05)

            force_delta = 0.05 * np.max(np.abs(self.force_over_time))
            self.force.set_ylim(np.min(self.force_over_time) - force_delta, np.max(self.force_over_time) + force_delta)

            pos_delta = 0.05 * np.max(np.abs(self.position_over_time))
            self.position.set_ylim(np.min(self.position_over_time) - pos_delta, np.max(self.position_over_time) + pos_delta)

            time.sleep(self.plot_delay)
