import Stepper.motor as mt
import logging

from time import sleep, time
from Stepper.tools import configreader
import timeit

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
    def __init__(self,motor,force_sensor,controller_q,test=False):
        logging.info('-----INITIALIZING EXPERIMENT------')
        logging.basicConfig(filename='experiment.log', filemode='w+',
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.ctrl_q = controller_q

        self.motor = motor

        self.fs = force_sensor

        #if set to True Gui can be run on a normal computer
        self.test=test





    def start(self,panel):

        [amplitudes, frequencies, cycletimes, waveforms, mode, waitingtimes, startingforce, startingspeed] = configreader("amplitudes",
                                                                                                           "frequencies",
                                                                                                           "cycletimes",
                                                                                                           "waveforms",
                                                                                                           "mode",
                                                                                                           "waitingtimes",
                                                                                                           "vorkraft",
                                                                                                            "startingspeed",
                                                                                                           category="experiment_config",
                                                                                                           file="Stepper/experimentconfig.cfg")


        amplitudes, frequencies, cycletimes, waitingtimes = amplitudes[1:-1].replace('\'','').split(","), frequencies[1:-1].replace('\'','').split(
            ","), cycletimes[1:-1].replace('\'','').split(","), waitingtimes[1:-1].replace('\'','').split(",")
        waveforms = waveforms[1:-1].split(",")

        cycle_count=0

        for amplitude,frequency, cycletime, waveform, waitingtime in zip(amplitudes,frequencies, cycletimes,waveforms, waitingtimes):
            cycle_count += 1
            print('starting cycle {}'.format(cycle_count))
            logging.info('-----STARTING CYCLE {}-----'.format(cycle_count))

            self.StartCycle(float(amplitude), float(frequency), int(cycletime), int(waveform), mode,startingforce, startingspeed)

            #self.EndCycle()


            logging.info('------CYCLE {} FINISHED------'.format(cycle_count))
            print('------CYCLE {} FINISHED------'.format(cycle_count))
            sleep(int(waitingtime))


        self.ctrl_q.put('KILL')



    def StartCycle(self, amplitude,frequency, cycletime, waveform, mode,startingforce,startingspeed):

        """
        :param amplitude:
        :param mode: Lasttyp von der Bioreaktor 'z' 'd' 'zdw' default 'd'
        :param frequency:
        :param waveform: "tri" for triangle "sin" for sinus
        :test: for development
        """

        if not self.test:
            self.motor.INITGPIO()

        cyclebeginpos = self.motor.position
        self.ctrl_q.put(True)
        logging.info('-------INITIALIZING START FORCE---------')

        self.initstartingforce(startingforce, startingspeed, mode)

        ##loop with time

        endtime = int(time()) + int(cycletime)
        i = 1
        while endtime > int(time()):

            control = self.ctrl_q.get()

            if control == "PAUSE":
                while True:
                    endtime += int(time())
                    sleep()
                    if self.ctrl_q == True:
                        break

            if control == "KILL":
                break
            else:
                self.ctrl_q.put(True)


            self.motor.move_one_period(amplitude, frequency ,waveform, mode)
            logging.info('-------Period {}--------'.format(i))
            print('period {} finished'.format(i))
            i += 1

    """

        if cyclebeginpos != self.motor.position:
            steps = self.motor.steps_per_rev(cyclebeginpos - self.motor.position)
            self.motor.move_steps(steps,'tri',2,0 if steps<cyclebeginpos else 1)

    """

    def EndCycle(self):
        self.motor.backtozero()
        if not self.test:
            self.motor.cleanGPIO()



    def initstartingforce(self,startingforce, startingspeed, mode):
        if self.test:
            return
        while self.fs.getreading() < float(startingforce):
            self.motor.move_up_down(0,self.test)
