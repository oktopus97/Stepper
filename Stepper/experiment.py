
import logging

from time import sleep, time
from Stepper.tools import configreader, computeLinearDelay, get_sin_table
import timeit
import Stepper.motor

"""
object Experiment :

    config:

    mode
    amplitudes
    frequencies
    waveforms
    cycletimes
    waitingtimes
    vorkraft


    __init__:
        defines instance of a Motor and a Force Sensor
        runs startExperiment(),


    startExperiment():
        reads the experiment config file
        initializes starting force (TODO)
        starts the experiment with the given config



"""

class Experiment(object):
    def __init__(self,motor,force_sensor,exp_q,info_q,test=False):
        logging.info('-----INITIALIZING EXPERIMENT------')
        logging.basicConfig(filename='experiment.log', filemode='w+',
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        self.exp_q = exp_q
        self.info_q = info_q
        self.motor = motor

        self.fs = force_sensor

        #if set to True Gui can be run on a normal computer
        self.test=test





    def start(self,panel):

        [amplitudes, frequencies, cycletimes, waveforms, mode, waitingtimes,repetitions, startingforce, startingspeed] = configreader("amplitudes",
                                                                                                           "frequencies",
                                                                                                           "cycletimes",
                                                                                                           "waveforms",
                                                                                                           "mode",
                                                                                                           "waitingtimes",
                                                                                                            "repetitions",
                                                                                                           "vorkraft",
                                                                                                            "startingspeed",
                                                                                                           category="experiment_config",
                                                                                                           file="Stepper/experimentconfig.cfg")


        amplitudes, frequencies, cycletimes, waitingtimes, repetitions = amplitudes[1:-1].replace('\'','').split(","), frequencies[1:-1].replace('\'','').split(
            ","), cycletimes[1:-1].replace('\'','').split(","), waitingtimes[1:-1].replace('\'','').split(","),repetitions[1:-1].replace('\'','').split(",")
        waveforms = waveforms[1:-1].split(",")

        cycle_count=0
        starttime = timeit.default_timer()
        
        self.exp_q.put(starttime)
        self.info_q.put((1,))
        
        logging.info('-------INITIALIZING START FORCE---------')
        self.initstartingforce(float(startingforce), float(startingspeed), mode)
        

        for amplitude,frequency, cycletime, waveform, waitingtime, rep in zip(amplitudes,frequencies, cycletimes,waveforms, waitingtimes, repetitions):
            
            cycle_count += 1
            self.info_q.put((amplitude, frequency, cycletime, cycle_count))

            #self.info_q.put((cycle_count,amplitude,frequency,waveform,cycletime))
            

            logging.info('-----STARTING CYCLE {}-----'.format(cycle_count))
            
            for rep in range(int(rep)):
                
                self.StartCycle(float(amplitude), float(frequency), int(cycletime), int(waveform), mode,startingforce, startingspeed,starttime)

                #self.EndCycle()
                sleep(int(waitingtime))
                

            logging.info('------CYCLE {} FINISHED------'.format(cycle_count))
            


        self.put()
        
    def put(self):
        self.exp_q.put("EXPERIMENT END")
        



    def StartCycle(self, amplitude,frequency, cycletime, waveform, mode,startingforce,startingspeed,starttime):
        """
        :param amplitude:
        :param mode: Lasttyp von der Bioreaktor 'z' 'd' 'zdw' default 'd'
        :param frequency:
        :param waveform: "tri" for triangle "sin" for sinus
        :test: for development
        """

        if not self.test:
            self.motor.INITGPIO()

        
        #self.ctrl_q.put(True)
        

        
        i=1 ##Getriebe Übersetzung
        step_count = int(float(amplitude)*self.motor.steps_per_rev*i)
        delay = computeLinearDelay(step_count, frequency) if waveform == 0 else get_sin_table(step_count,frequency)

        no_periods = int(cycletime*frequency)
        start=int(time())
        
        for i in range(no_periods):
            """
            control = self.ctrl_q.get()
            print(control)


            if control == "KILL":
                self.stp = True
                break

            else:
                self.ctrl_q.put(True)

            """
            self.motor.move_one_period(step_count,delay, mode, starttime)
        print(int(time()) - start)
            
            
    
            

    """

        if cyclebeginpos != self.motor.position:
            steps = self.motor.steps_per_rev(cyclebeginpos - self.motor.position)
            self.motor.move_steps(steps,'tri',2,0 if steps<cyclebeginpos else 1)

    """

    def EndCycle(self):
        
        if not self.test:
            self.motor.cleanGPIO()



    def initstartingforce(self,startingforce, startingspeed, mode):
        if self.test:
            return
        if startingforce != "":
            while self.fs.getreading() < float(startingforce):
                self.motor.move_up_down(0,self.test)
"""
motor = motor.Motor(None,None)
experiment = Experiment(motor,None,None,None,None,None)
import GUI.multiprocess as mp
manager = mp.Management()
manager.work(experiment.start,(None,))
"""