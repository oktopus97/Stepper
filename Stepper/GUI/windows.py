#abim gözünü seviyim bi düzenle
from gui_tools import cao, inputsizer
import sys,os
sys.path.append(os.getcwd())
from Stepper.tools import configwriter
import wx
from wxasync import StartCoroutine
from time import sleep

from plotter import Plotter
from threading import Thread, Lock
from queue import Queue
import asyncio
from events import CloseEvent, EVT_CLS

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

    def Start(self):
        self.startpanel.Hide()
        if self.startpanel.manual_panel.is_activated:
            self.startpanel.manual_panel.deactivate()


        self.exp_panel.build()
        self.Fit()
        self.end = ExperimentEnd(self)
        self.exp_panel.start()


class ExperimentPanel(wx.Panel):
    def __init__(self,parent):
        self.parent = parent
        super().__init__(self.parent)
        self.controller = parent.controller


        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.plot = PlotPanel(self,self.parent.controller,self.parent.management)

        self.ctrl_toolbar = ExperimentToolbar(self)
        self.infotext = wx.StaticText(self, label = 'loooo')

        self.vbox.Add(self.ctrl_toolbar,0,wx.ALL|wx.EXPAND,0)
        self.vbox.Add(self.plot,1,wx.ALL|wx.EXPAND,0)
        self.vbox.Add(self.infotext,1,wx.ALL|wx.EXPAND,0)
        #event cls will be triggered with gui_q
        self.Bind(EVT_CLS,self.OnClose)
        self.Hide()

    def updateinfo(self):
        while True:
            info = self.controller.exp_info_q.get()
            if info == 'KILL':
                return
            self.infotext.SetLabel('Cycle {}, Amplitude {}, Frequency {}, Waveform {}, Duration {}'.format(*info))
            self.Layout()

    def stop_callback(self):
        #experiment gives the stop signal
        while True:
            gui_cmd = self.controller.gui_q.get()
            if gui_cmd == 'KILL':
                self.controller.exp_info_q.put(gui_cmd)
                self.GetEventHandler().ProcessEvent(CloseEvent())
                return
            else:
                continue

    def start(self):
        self.plot.plot_thread.start()

        self.worker_id = self.parent.management.work(function=self.parent.controller.start_experiment, args=(self,))
        self.callback = Thread(target=self.stop_callback, daemon = True)
        self.callback.start()
        self.info = Thread(target=self.updateinfo,daemon = True)
        self.info.start()
    def build(self):
        self.vbox.SetSizeHints(self)
        self.SetSizer(self.vbox)
        self.Layout()
        self.Show()


    def OnClose(self,e):

        self.Hide()

        self.parent.end.Show()



class ExperimentToolbar(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Stop = wx.Button(self,id=wx.ID_ANY,label='Stop')

        self.sizer.Add(self.Stop,0,wx.EXPAND,0)



        self.Bind(wx.EVT_BUTTON,self.OnStop, self.Stop)


        self.parent=parent

        #sometimes the screen doesn't fit, that's why Fit() fkt is called after SetSizerAndFit()
        self.SetSizerAndFit(self.sizer)
        self.Fit()



    def OnStop(self, e):

        self.parent.controller.control('KILL')





class PlotPanel(wx.Panel):
    def __init__(self,parent,controller,manager):
        self.parent = parent
        super().__init__(self.parent)

        self.pos_q, self.force_q = controller.motor.pos_q, controller.force_sensor.force_q
        self.ctrl_q = controller.plot_control

        self.manager = manager

        self.draw_q = manager.Queue()

        self.plt = Plotter(self, self.pos_q, self.force_q,self.ctrl_q)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.plt,0,wx.ALL|wx.EXPAND,0)

        plot_stop_q = Queue()

        self.plot_thread = Thread(target=self.plt.plotting,args=(plot_stop_q,), daemon=True)



        self.SetSizerAndFit(self.sizer)

    def join_plot(self):

        self.plot_thread.join()

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
        self.Hide()
        self.parent.startpanel.Show()
    def OnExit(self,e):
        self.parent.OnExit(e)





class StartPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.old_conf = wx.Button(self,-1,'Start the Experiment')
        self.new_conf =  wx.Button(self, -1, 'Set new configuration')

        self.Bind(wx.EVT_BUTTON,self.OnNewConf, self.new_conf)
        self.Bind(wx.EVT_BUTTON,self.OnGo, self.old_conf)


        self.sizer.Add(self.old_conf,0,wx.EXPAND,0)
        self.sizer.Add(self.new_conf,0,wx.EXPAND,0)


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
            self.controller.motor.move_up_down(dir)
            if dir is None:
                break


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
        self.text = wx.StaticText(self, label='Force Sensor Calibration, \n Please put 100g weight on the Force Sensor and push the button')
        self.button = wx.Button(self,-1, 'GO')

        self.sizer.Add(self.text,0,wx.EXPAND,0)
        self.sizer.Add(self.button,0,wx.EXPAND,0)

        self.button.Bind(wx.EVT_BUTTON, self.OnGO)
        self.fs =  self.parent.controller.force_sensor
        self.SetSizerAndFit(self.sizer)
        self.readfkt = self.fs.getreading

        self.ShowModal()

    def OnGO(self,e):

        self.first = self.average_readings(20)
        self.text.SetLabel('Now put 200g and press the button')
        self.Layout()
        self.button.Unbind(wx.EVT_BUTTON)
        self.button.Bind(wx.EVT_BUTTON, self.OnSecondGo)

    def OnSecondGo(self,e):
        self.second = self.average_readings(20)
        self.calibrate()
        self.Destroy()


    def calibrate(self):

        difference = self.second - self.first

        multiplier = 0.9807/difference
        offset = self.first - difference

        self.fs.multiplier, self.fs.offset = multiplier,offset

    def average_readings(self,iter):
        #get the average of iter readings

        readings = []
        for i in range(iter):
            readings.append(self.readfkt())
        return mean(readings)


class Conf(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent)
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
        configwriter('Stepper/config.cfg','manual_config', feature_names,features)
    def OnOK(self,e):
        self.OnApply(e)
        self.OnClose(e)
        return


class MotorConfigPanel(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.cfg = 'motorconfig.cfg'
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.motor_specs = [('Step Angle',"1.8"), ('Resolution',"1/8")]
        self.GPIO_config = [('GPIO Mode','BCM'), ('Dir Pin', "20"), ('Step Pin',"18"), ('Mode0',"14"),('Mode1',"15"),('Mode2',"21")]
        self.inputs = []
        self.sizer.Add(wx.StaticText(self, label='Motor Specifications:'),0,wx.EXPAND,0)
        for spec_tuple in self.motor_specs:
            spec_tuple = spec_tuple + (self,)
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
            features.append(input.GetValue())
        configwriter('Stepper/motorconfig.cfg','motor_config', feature_names,features)
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

        for index, input in enumerate(self.inputs[2:]):
            if index != 0:
                waitingtimes.append(input[0].GetValue())
                i = 1
            else:
                i = 0

            amplitudes.append(input[i].GetValue())
            frequencies.append(input[i+1].GetValue())
            cycletimes.append(input[i+2].GetValue())
            waveforms.append(input[i+3].GetSelection())


        waitingtimes.append('0')
        feature_names = ['vorkraft','mode','amplitudes', 'frequencies','waveforms','cycletimes','waitingtimes']
        configwriter("Stepper/experimentconfig.cfg", "experiment_config", feature_names, vorkraft,mode, amplitudes,frequencies,waveforms,cycletimes,waitingtimes)
        self.Close()
        self.parent.OnGo(e)



def add_cycle(parent,count):
    cycle_options = [('Waiting Time',None, parent)] if count != 1 else []
    cycle_options += [('Amplitude',None, parent), ('Frequency', None, parent), ('Cycle Time', None,parent), ('Waveform',('Triangular','Sinus',),parent)]
    cycle_sizer = wx.BoxSizer(wx.VERTICAL)
    cycle_inputs = []

    cycle_sizer.Add(wx.StaticText(parent,label='Cycle {}'.format(count)),0, wx.EXPAND,0)

    for spec_tuple in cycle_options:
        sizer, input = inputsizer(spec_tuple)
        cycle_sizer.Add(sizer,0,wx.EXPAND,0)
        cycle_inputs.append(input)


    return cycle_sizer, cycle_inputs
