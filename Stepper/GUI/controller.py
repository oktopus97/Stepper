import sys,os
sys.path.append(os.getcwd())
from Stepper.experiment import Experiment
from Stepper.motor import Motor, ForceSensor

class ExperimentController(object):
    def __init__(self,exp_controller_q,plot_ctrl_q , pos_q,force_q,gui_q,exp_info_q,test):


        self.force_sensor = ForceSensor(force_q,test)
        self.motor = Motor(pos_q,self.force_sensor,test)
        self.controller_q = exp_controller_q
        self.plot_control = plot_ctrl_q
        self.gui_q = gui_q
        self.exp_info_q = exp_info_q
        """
        Controller commands:
        "KILL" ends the Experiment
        "PAUSE" pauses the Experiment
        True experiment
        """
    def control(self, cmd):
        self.controller_q.put(cmd)
        self.plot_control.put(cmd)

    def start_experiment(self,panel):
        self.panel = panel
        self.experiment = Experiment(self.motor, self.force_sensor, self.controller_q,self.gui_q,self.exp_info_q, self.control)
        self.control(True)
        self.experiment.start(panel)


    def end_experiment(self):
        self.panel.OnClose(e=None)
