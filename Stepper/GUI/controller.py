import sys,os
sys.path.append(os.getcwd())
from Stepper.experiment import Experiment
from Stepper.motor import Motor, ForceSensor

class ExperimentController(object):
    def __init__(self,exp_q,info_q,test):

        self.exp_q = exp_q
        self.info_q = info_q
        self.force_sensor = ForceSensor(test)
        self.motor = Motor(self.force_sensor,test)
        
        """
        Controller commands:
        "KILL" ends the Experiment
        "PAUSE" pauses the Experiment
        True experiment
        """
    def start_experiment(self,panel):
        self.panel = panel
        self.experiment = Experiment(self.motor, self.force_sensor,self.exp_q, self.info_q)
        self.experiment.start(panel)


    def end_experiment(self):
        self.panel.OnClose(e=None)
