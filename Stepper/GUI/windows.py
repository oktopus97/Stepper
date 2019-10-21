#abim gözünü seviyim bi düzenle
from gui_tools import cao, inputsizer
import sys,os
sys.path.append(os.getcwd())
from Stepper.tools import configwriter
import wx
from time import sleep, time
import timeit

from plot import Plotter
from threading import Thread, Lock
from queue import Queue
import asyncio
from events import CloseEvent, EVT_CLS, PlotEvent, EVT_PLT
from Stepper.constants import amp_range,freq_range, plot_delay

from statistics import mean

manually_moved = False

class MainWindow(wx.Frame):
    def __init__(self,parent,controller,management):
        super().__init__(parent=parent)
        self.controller = controller
        
        self.management = management
        self.startpanel = StartPanel(self)



        #set up menus
        filemenu= wx.Menu()
        menuAbout= filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open Configuration File","Open Custom Config")
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

        editmenu = wx.Menu()
        motorconfig = editmenu.Append(wx.ID_ANY,"&Motor Configuration", "Configure Motor")
        config = editmenu.Append(wx.ID_EXECUTE,"&Preferences", "set Preferences")
        calibrate = editmenu.Append(wx.ID_ANY,"&Calibrate", "Calibrate Force Sensor")
        #set up the menubar
        menubar = wx.MenuBar()
        menubar.Append(filemenu,"&File")
        menubar.Append(editmenu,"&Edit")
        self.SetMenuBar(menubar)

        #bind events

        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)

        self.Bind(wx.EVT_MENU, self.OnMotorConf, motorconfig)
        self.Bind(wx.EVT_MENU, self.OnCalibrate, calibrate)
        self.Bind(wx.EVT_MENU, self.OnConf, config)
        self.exp_panel = ExperimentPanel(self)

        #show the frame
        self.startpanel.Layout()
        self.startpanel.Show()
        self.Show()

    def OnCalibrate(self,e):
        dlg = FSCalibrate(self)


    def OnAbout(self, e):
        dlg = wx.MessageDialog(self, "An open source Application for controlling\
                                      Stepper Motor powered Bioreactors\
                                      contributors:\
                                      oktopus97, drwxars","About", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self, e):
        self.OnClose(e)


    def OnClose(self,e):
        self.Close(True)

    def OnMotorConf(self,e):
        motorconfig = MotorConfigPanel(self)
        motorconfig.ShowModal()

    def OnConf(self,e):
        conf = Conf(self)
        conf.ShowModal()

    def Start(self,test=False):
        self.startpanel.Hide()
        if self.startpanel.manual_panel.is_activated:
            self.startpanel.manual_panel.deactivate()


        self.exp_panel.build()
        self.Fit()
        self.end = ExperimentEnd(self)
        self.exp_panel.start(test)


class ExperimentPanel(wx.Panel):
    def __init__(self,parent):
        self.parent = parent
        super().__init__(self.parent)
        self.controller = parent.controller


        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.plot = PlotPanel(self,self.parent.controller,self.parent.management)

        self.ctrl_toolbar = ExperimentToolbar(self, self.controller.info_q)
        
        self.vbox.Add(self.ctrl_toolbar,0,wx.ALL|wx.EXPAND,0)
        self.vbox.Add(self.plot,1,wx.ALL|wx.EXPAND,0)
        
        #event cls will be triggered with gui_q
        self.Bind(EVT_CLS,self.OnClose)
        self.Hide()
        self.worker_id = None
    """
    def updateinfo(self):
        while True:
            info = self.controller.exp_info_q.get()
            if info == 'KILL':
                return
            wx.CallAfter(self.infotext.SetLabel,'Cycle {}, Amplitude {}, Frequency {}, Waveform {}, Duration {}'.format(*info))
            self.Layout()
    """

    def stop_callback(self):
        #experiment gives the stop signal
        while True:
            cmd = self.controller.exp_q.get()
            if cmd == 'EXPERIMENT END':
                self.GetEventHandler().ProcessEvent(CloseEvent())
                return
            else:
                continue
    
    def start(self, test=False):
        if not test:
            self.worker_id = self.parent.management.work(function=self.parent.controller.start_experiment, args=(self,))
            start_time = self.controller.exp_q.get()
            self.callback = Thread(target=self.stop_callback, daemon = True)
            self.callback.start()
        else:
            start_time = time()
        self.plot.start_reading_thread(start_time)
        
        self.plot.plt.set_start(start_time)
        self.plot.timer.Start(plot_delay)
        
        """
        self.info = Thread(target=self.updateinfo,daemon = True)
        self.info.start()
        """
    def build(self):
        self.vbox.SetSizeHints(self)
        self.SetSizer(self.vbox)
        self.Layout()
        self.Show()


    def OnClose(self,e):
        self.plot.timer.Stop()
        self.plot.join_plot()
        

        self.Hide()

        self.parent.end.Show()
        
    def OnHome(self,e):
        self.plot.timer.Stop()
        self.test_button.Hide()
        self.Hide()
        self.parent.Show()


class ExperimentToolbar(wx.Panel):
    def __init__(self, parent,info_q):
        super().__init__(parent)
        self.info_q = info_q
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Stop = wx.Button(self,id=wx.ID_ANY,label='Stop')
        
        self.sizer.Add(self.Stop,0,wx.EXPAND,0)



        self.Bind(wx.EVT_BUTTON,self.OnStop, self.Stop)


        self.parent=parent

        #sometimes the screen doesn't fit, that's why Fit() fkt is called after SetSizerAndFit()
        self.SetSizerAndFit(self.sizer)
        self.Fit()

    
    def OnStop(self, e):
        if self.parent.worker_id is None:
            self.parent.Hide()
            self.parent.plot.timer.Stop()
            self.parent.plot.plt.clear()
            self.parent.plot.join_plot()
            
            self.parent.parent.startpanel.Show()
            self.parent.parent.startpanel.manual_panel.activate()
            return
        
        self.parent.parent.management.terminate(self.parent.worker_id)
        self.parent.parent.controller.motor.backtozero()
        self.parent.OnClose(e)





class PlotPanel(wx.Panel):
    def __init__(self,parent,controller,manager):
        self.parent = parent
        super().__init__(self.parent)

        self.manager = manager

        self.plt = Plotter(self, parent.parent.controller.force_sensor.getreading, controller.experiment.exp_str)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.plt,0,wx.ALL|wx.EXPAND,0)
        self.timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.plt.update)


        self.SetSizerAndFit(self.sizer)
    def start_reading_thread(self,start_time):
        self.plt.reading=True
        self.plot_thr = Thread(target=self.plt.read, args=(start_time,), daemon=True)
        self.plot_thr.start()
    def join_plot(self):
        self.plt.reading = False
        self.plot_thr.join()

    def end(self):
        parent.OnClose(None)

class ExperimentEnd(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.Text = wx.StaticText(self,label='EXPERIMENT ENDED')
        self.BackHomeButton = wx.Button(self, -1,'Back Home')
        self.ExitButton = wx.Button(self, -1,'Exit')

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.bsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bsizer.Add(self.BackHomeButton,0,wx.EXPAND,0)
        self.bsizer.Add(self.ExitButton,0,wx.EXPAND,0)

        self.sizer.Add(self.Text,0,wx.EXPAND,0)
        self.sizer.Add(self.bsizer,0,wx.EXPAND,0)
        self.SetSizerAndFit(self.sizer)
        self.Layout()
        self.Hide()
        self.Bind(wx.EVT_BUTTON,self.OnBackHome, self.BackHomeButton)
        self.Bind(wx.EVT_BUTTON,self.OnExit, self.ExitButton)

    def OnBackHome(self,e):
        import os
        pid = os.getpid()
        os.system(os.getcwd()+"/Stepper/GUI/newapp.sh "+str(pid))
        
    def OnExit(self,e):
        self.parent.OnExit(e)





class StartPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.old_conf = wx.Button(self,-1,'Start the Experiment')
        self.new_conf =  wx.Button(self, -1, 'Set new configuration')
        self.test =  wx.Button(self, -1, 'Test the Force Measurement')

        self.Bind(wx.EVT_BUTTON,self.OnNewConf, self.new_conf)
        self.Bind(wx.EVT_BUTTON,self.OnGo, self.old_conf)
        self.Bind(wx.EVT_BUTTON,self.OnTest, self.test)


        self.sizer.Add(self.old_conf,0,wx.EXPAND,0)
        self.sizer.Add(self.new_conf,0,wx.EXPAND,0)
        self.sizer.Add(self.test,0,wx.EXPAND,0)


        self.movementsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.movementsizer.Add(wx.StaticText(self,label=" Manual Motor Movement                 "),0,wx.LEFT,0)



        self.manual_panel = ManualMovementPanel(self,parent.management,self.parent.controller)

        self.movementsizer.Add(self.manual_panel,0,wx.RIGHT,0)
        self.sizer.Add(self.movementsizer,0,wx.EXPAND,0)

        self.sizer.SetSizeHints(self)
        self.SetSizer(self.sizer)


    def OnNewConf(self,e):
        dlg = ExperimentConfigPanel(self)
        dlg.ShowModal()
    def OnGo(self,e):

        self.parent.Start()
    def OnTest(self, e):
        self.parent.Start(True)



class ManualMovementPanel(wx.Panel):
    def __init__(self,parent,manager,controller):
        super().__init__(parent)
        self.management = manager
        self.controller = controller
        self.activate()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.up = wx.Button(self,id=wx.ID_UP)
        self.down = wx.Button(self, id=wx.ID_DOWN)
        self.SetSizer(self.sizer)


        for button in self.up, self.down:
            self.sizer.Add(button,0,wx.EXPAND,0)



        self.up.Bind(wx.EVT_BUTTON,self.OnUp)
        self.down.Bind(wx.EVT_BUTTON,self.OnDown)

    def move(self,q):
        while self.is_activated:
            dir = q.get()
            if dir is None:
                break
            self.controller.motor.move_up_down(dir)
            


    def activate(self):
        self.q = self.management.Queue()
        self.is_activated = True
        self.process_id = self.management.work(function= self.move,args=(self.q,))
    def deactivate(self):
        if not self.is_activated:
            raise RuntimeError('Please Activate First :)')

        self.is_activated = False
        self.q.put(None)
        self.management.join(self.process_id)

    def OnUp(self,e):
        self.q.put(True)

    def OnDown(self,e):
        self.q.put(False)


#config panels
class FSCalibrate(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.text = wx.StaticText(self, label='Force Sensor Calibration, \n Please put 50g weight on the Force Sensor and push the button')
        self.button = wx.Button(self,-1, 'GO')
        

        self.sizer.Add(self.text,0,wx.EXPAND,0)
        self.sizer.Add(self.button,0,wx.EXPAND,0)

        self.button.Bind(wx.EVT_BUTTON, self.OnGO)
        self.fs =  self.parent.controller.force_sensor
        self.SetSizerAndFit(self.sizer)
        self.readfkt = self.fs.getreading
        sleep(3)
        self.zero = self.average_readings(20)
        

        self.ShowModal()

    def OnGO(self,e):
        sleep(3)

        self.first = self.average_readings(50)
        
        self.text.SetLabel('Now put 100g and press the button')
        self.Layout()
        self.button.Unbind(wx.EVT_BUTTON)
        self.button.Bind(wx.EVT_BUTTON, self.OnSecondGo)

    def OnSecondGo(self,e):
        sleep(3)
        self.second = self.average_readings(50)
        self.calibrate()
        self.Destroy()


    def calibrate(self):
        

        diff = self.second - self.first
        
        multiplier = 0.9807/(diff*2)
        offset = self.zero

        configwriter('Stepper/motorconfig.cfg','calibration', ["multiplier", "offset"],multiplier, offset)

    def average_readings(self,iter):
        #get the average of iter readings

        reading_sum = 0
        for i in range(iter):
            #get raw reading
            reading_sum += (self.readfkt(raw=True))
           
        return reading_sum/iter
        
class FalseConf(wx.Dialog):
    def __init__(self,parent, feature):
        super().__init__(parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(wx.StaticText(self, label='Please give a valid Value for {}'.format(feature)),0,wx.EXPAND,0)
        self.button = wx.Button(self, -1, "Close")
        self.sizer.Add(self.button,0,wx.EXPAND,0)
        
        self.button.Bind(wx.EVT_BUTTON,self.OnClose)
        self.Layout()
        self.sizer.SetSizeHints(self)
        self.SetSizerAndFit(self.sizer)
        self.ShowModal()
        
    def OnClose(self,e):
        self.Close()
        
class Conf(wx.Dialog):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(self.parent)
        self.cfg = 'manual.cfg'
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.specs = [('Manual Motor Speed (mm/s)','1'), ('Starting Speed','1')]
        self.inputs = []

        for spec_tuple in self.specs:
            spec_tuple = spec_tuple + (self,)
            sizer, input = inputsizer(spec_tuple)
            self.sizer.Add(sizer,0,wx.EXPAND,0)
            self.inputs.append(input)

        self.caosizer, self.close, self.apply, self.ok = cao(self)

        self.sizer.Add(self.caosizer)

        self.Layout()
        self.sizer.SetSizeHints(self)
        self.SetSizerAndFit(self.sizer)

    def OnClose(self,e):
        self.Close()
    def OnApply(self,e):
        feature_names = []
        features = []
        for index, input in enumerate(self.inputs):
            feature_names.append(self.specs[index][0])
            features.append(input.GetValue())
        configwriter('Stepper/config.cfg','manual_config', feature_names,*features)
        self.parent.controller.motor.update_features()
    def OnOK(self,e):
        self.OnApply(e)
        self.OnClose(e)
        return


class MotorConfigPanel(wx.Dialog):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(self.parent)
        self.cfg = 'motorconfig.cfg'
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.motor_specs = [('Step Angle',"1.8"), ('Resolution',"1/8", ("1/8","Full","Half","1/4","1/2","1/16","1/32",))]
        self.GPIO_config = [('GPIO Mode','BCM'), ('Dir Pin', "20"), ('Step Pin',"21"), ('Mode0',"14"),('Mode1',"15"),('Mode2',"18")]
        self.inputs = []
        self.sizer.Add(wx.StaticText(self, label='Motor Specifications:'),0,wx.EXPAND,0)
        for spec_tuple in self.motor_specs:
            spec_tuple = spec_tuple[0:2] + (self,)
            sizer, input = inputsizer(spec_tuple)
            self.sizer.Add(sizer,0,wx.EXPAND,0)
            self.inputs.append(input)

        self.sizer.Add(wx.StaticText(self, label='GPIO Settings:'),0,wx.EXPAND,0)

        for spec_tuple in self.GPIO_config:
            spec_tuple = spec_tuple + (self,)
            sizer, input = inputsizer(spec_tuple)
            self.sizer.Add(sizer,0,0,0)
            self.inputs.append(input)


        self.caosizer, self.close, self.apply, self.ok = cao(self)

        self.sizer.Add(self.caosizer)

        self.Layout()
        self.sizer.SetSizeHints(self)
        self.SetSizerAndFit(self.sizer)
    def OnClose(self,e):
        self.Close()
    def OnApply(self,e):
        feature_list = self.motor_specs + self.GPIO_config

        feature_names = []
        features = []
        for index, input in enumerate(self.inputs):
            feature_names.append(feature_list[index][0])
            input_val = input.GetValue()
            
            if len(feature_list[index]) == 3 and input_val not in feature_list[index][2]:
                dlg = FalseConf(self.parent,feature_list[index][0])
                return
                
            
            features.append(input_val)
        configwriter('Stepper/motorconfig.cfg','motor_config', feature_names,*features)
        self.parent.controller.motor.update_features()
        
    def OnOK(self,e):
        self.OnApply(e)
        self.OnClose(e)
        return


class ExperimentConfigPanel(wx.Dialog):
    def __init__(self,parent):
        super().__init__(parent=parent)
        self.parent=parent


        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.cycles = wx.GridSizer(3,6,1,1)

        self.inputs = []


        #Settings that stay the same for all Cycles
        self.specs = [('Starting Force',None,self,),('Bioreactor Force Type',('Push','Pull',),self,)]
        for tuple in self.specs:

            sizer, input = inputsizer(tuple)
            self.inputs.append(input)
            self.sizer.Add(sizer,0,wx.EXPAND,0)

        self.cycle_count = 1

        sizer, cycle_inputs = add_cycle(self, self.cycle_count)
        self.inputs.append(cycle_inputs)


        self.cycles.Add(sizer,0,wx.EXPAND,0)

        self.sizer.Add(self.cycles,0,wx.EXPAND,0)


        add_cycle_btn = wx.Button(self,-1,'Add New Cycle')
        self.Bind(wx.EVT_BUTTON, self.OnAddCycle, add_cycle_btn)
        self.sizer.Add(add_cycle_btn,0,wx.EXPAND,0)

        self.remove_cycle_btn = wx.Button(self,-1,'Remove Last Cycle')
        self.Bind(wx.EVT_BUTTON, self.OnRemoveCycle, self.remove_cycle_btn)
        self.sizer.Add(self.remove_cycle_btn,0,wx.EXPAND,0)

        self.remove_cycle_btn.Disable()

        self.rst_cycle_btn = wx.Button(self,-1,'Reset')
        self.Bind(wx.EVT_BUTTON, self.OnResetCycle, self.rst_cycle_btn)
        self.sizer.Add(self.rst_cycle_btn,0,wx.EXPAND,0)

        self.rst_cycle_btn.Disable()

        start_button = wx.Button(self,-1,'Start Experiment')
        self.Bind(wx.EVT_BUTTON, self.OnStart, start_button)
        self.sizer.Add(start_button,0,wx.EXPAND,0)
        self.SetSizerAndFit(self.sizer)




    def OnAddCycle(self, e):
        self.cycle_count += 1
        self.remove_cycle_btn.Enable()
        self.rst_cycle_btn.Enable()


        sizer, cycle_inputs = add_cycle(self,self.cycle_count)
        self.inputs.append(cycle_inputs)

        self.cycles.Add(sizer,0,wx.EXPAND,0)
        self.Layout()
        self.Fit()

    def OnRemoveCycle(self,e):

        self.cycle_count -= 1
        self.inputs.pop()
        children = self.cycles.GetChildren()
        children[-1].DeleteWindows()
        self.cycles.Layout()
        self.remove_cycle_btn.Disable()

    def OnResetCycle(self,e):
        self.Destroy()
        self.parent.OnNewConf(e)
    def OnStart(self,e):
        vorkraft, mode = self.inputs[0].GetValue(),self.inputs[1].GetSelection()





        amplitudes = []
        frequencies = []
        waveforms = []
        cycletimes = []
        waitingtimes = []
        repetitions = []
        
        

        for index, input in enumerate(self.inputs[2:]):
            amp, freq = input[0].GetValue(),input[1].GetValue()
            
            if not amp_range[0] <= float(amp) <= amp_range[1]:
                dlg = FalseConf(self.parent,"Amplitude")
                return
            elif not freq_range[0] <= float(freq) <=freq_range[1]:
                dlg = FalseConf(self.parent,"Frequency")
                return
                
            
            
            amplitudes.append(amp)
            frequencies.append(freq)
            cycletimes.append(input[2].GetValue())
            waveforms.append(input[3].GetSelection())
            waitingtimes.append(input[4].GetValue())
            repetitions.append(input[5].GetValue())


        waitingtimes.append('0')
        feature_names = ['vorkraft','mode','amplitudes', 'frequencies','waveforms','cycletimes','waitingtimes', "repetitions"]
        configwriter("Stepper/experimentconfig.cfg", "experiment_config", feature_names, vorkraft,mode, amplitudes,frequencies,waveforms,cycletimes,waitingtimes,repetitions)
        self.Close()
        self.parent.OnGo(e)



def add_cycle(parent,count):
    cycle_options = [('Amplitude [mm]',None, parent), ('Frequency [Hz]', None, parent), ('Cycle Time [s]', None,parent), ('Waveform',('Triangular','Sinus',),parent),('Waiting Time [s]',None, parent),('Repetitions',None, parent)]
    cycle_sizer = wx.BoxSizer(wx.VERTICAL)
    cycle_inputs = []

    cycle_sizer.Add(wx.StaticText(parent,label='Cycle {}'.format(count)),0, wx.EXPAND,0)

    for spec_tuple in cycle_options:
        sizer, input = inputsizer(spec_tuple)
        cycle_sizer.Add(sizer,0,wx.EXPAND,0)
        cycle_inputs.append(input)


    return cycle_sizer, cycle_inputs
