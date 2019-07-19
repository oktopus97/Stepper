import sys,os
sys.path.append(os.getcwd())
from Stepper.experiment import Experiment
from Stepper.motor import Motor, ForceSensor

class ExperimentController(object):
    def __init__(self,controller_q, pos_q,force_q,test):


        self.force_sensor = ForceSensor(force_q,test)
        self.motor = Motor(pos_q,self.force_sensor,test)
        self.controller_q = controller_q
        """
        Controller commands:
        "KILL" ends the Experiment
        "PAUSE" pauses the Experiment
        True experiment
        """

    def start_experiment(self,panel):
        self.panel = panel
        self.experiment = Experiment(self.motor, self.force_sensor, self.controller_q)
        self.experiment.start(panel)


    def end_experiment(self):
        self.panel.OnClose(e=None)
