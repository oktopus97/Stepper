from time import sleep
from Stepper.tools import computeLinearDelay, configreader,get_sin_table
from Stepper.constants import  RESOLUTION_DICT
from matplotlib import pyplot as plt
import timeit
from matplotlib import pyplot as plt
import numpy as np

#from config import step_angle, dir, step, m1, m2, m3 , gpio_mode


"""
object Motor:

    config:

        step_angle
        resolution

        gpio_mode
        (PINS)
        dir
        step
        m1
        m2
        m3


    __init__:        self.adc = Adafruit_ADS1x15.ADS1015()
        reads the motor config and initializes the motor parameters

    move_one_period():
        performs an up and a down movement (mode argument is the pull or press setting TODO)

    move_steps():
        move with constant speed with the given step count. used for the movements other than the experiment like the application
        of the starting force

    INITGPIO():
        initializes GPIO ports
    cleanGPIO():
        cleans GPIO ports

object ForceSensor:

    get_reading():
        gets the reading from the sensor
"""




class Motor(object):
    """
    initialize a motor class with default position x = 0
    params:
    step_angle in Degrees(default 1.8)
    coef : step coefficient, default 1 for Full step

    RasPi pins(mode = BCM):

    dir (def = 20)
    step (def = 21)
    m1 (def = 14)
    m2 (def = 15)
    m3 (def = 18)

    """
    def __init__(self,pos_q,force_sensor,test=False):
        self.position = 0
        self.pos_q=pos_q
        self.fs=force_sensor
        #test variablen
        self.c_bilanz = 0
        self.pos = []
        ##reading settings from file



        [self.gpio_mode, self.resolution,self.angle, self.dir, self.step, self.m1,self.m2,self.m3] =  configreader('gpio_mode',"resolution",'step_angle','dir',
                                                                                          'step','m1','m2','m3',category='motor_config',
                                                                                                                   file="Stepper/motorconfig.cfg")
        self.step, self.dir, self.m1, self.m2, self.m3 = int(self.step), int(self.dir),int(self.m1),int(self.m2),int(self.m3)
        self.mode = (self.m1, self.m2, self.m3)

        self.manual_speed =  int(configreader('manual motor speed (mm/s)', category='manual_config', file='Stepper/config.cfg')[0][2:-2])
        print(self.manual_speed)




        self.steps_per_rev = int(360/float(self.angle))*RESOLUTION_DICT[self.resolution][1]
        self.test = test
        if not test:
            import GPIO


    def move_one_period(self, amplitude, frequency, waveform, mode):
        """
        Moves the motor one period
        :param mode: Lasttyp von der Bioreaktor 'z' 'd'  default 'd'
        :param distance: in mm positive for up negative for down
        """

        ##computing the step count for the given amplitude and resolution coef
        i = 1 #getriebe übersetzung 1mm/rev bei unserem BioReaktor
        step_count = int(float(amplitude)*self.steps_per_rev*i)

        basedir = True if mode == "0" else False

        dir = basedir ##1 for down
        self.move_steps(step_count, frequency,dir, waveform=waveform)
        #GPIO.move_periodPWM(self, self.step, self.dir, frequency, step_count, dir,waveform, mode)



        dir = not basedir
        self.move_steps(step_count, frequency,dir, waveform=waveform,reverse_delays=True)

        #GPIO.move_periodPWM(self, self.step,self.dir,  frequency,step_count,dir,waveform, mode)


    def move_steps(self, step_count, frequency, dir, waveform = 0,delay =None,reverse_delays=False):
        if waveform == 1:
            delay_list = get_sin_table(step_count,frequency)
            if reverse_delays:
                delay_list  = delay_list[::-1]
        else:
            if delay is None:
                delay = computeLinearDelay(step_count, frequency)
            else:
                delay = delay


        if not self.test:
            GPIO.setdir(dir,self.dir)

        for i in range(int(step_count)):

            if not dir:
                c = 1
            else:
                c = -1
            if waveform==1:
                delay = delay_list[i]



            self.position = np.add(self.position, c/self.steps_per_rev)
            self.put_reading()

            if not self.test:
                GPIO.step_pulse(delay,self.step)

            sleep(delay)

        return delay

    def put_reading(self):
        self.pos_q.put(self.position)
        self.fs.put_reading()

    def move_up_down(self, dir):
        #zero for up

        #compute the step count and freq for 1 mm in 1 mm/s
        steps = self.steps_per_rev/10
        freq = 1/4 * self.manual_speed ## adjust speed

        #move it
        self.move_steps(steps, freq, dir)



    def backtozero(self):
        return
        steps = self.position*self.steps_per_rev
        frequency = (self.position/4)# adjust speed
        self.move_steps(steps,frequency,dir=0)
        self.position = 0



    ##open gpio ports
    def openPorts(self, *args, **kwargs):
        if not self.test:
            GPIO.initGPIO(args, mode=kwargs["mode"])

    def INITGPIO(self):
        self.openPorts(self.step, mode = self.gpio_mode)
        self.openPorts(self.dir,mode = self.gpio_mode)
        self.openPorts(self.m1, self.m2, self.m3,  mode = self.gpio_mode)
        if not self.test:
            GPIO.set_mode(self.mode,RESOLUTION_DICT[self.resolution][0])
        self.GPIO_OUTPUTS=True



    def cleanGPIO(self):
        if not self.test:
            GPIO.cleanGPIO()
        self.GPIO_OUTPUTS = False



class ForceSensor():
    def __init__(self,force_q,test=False):
        self.force_q=force_q
        self.test=test
        if not self.test:
            self.adc = Adafruit_ADS1x15.ADS1015()
        self.GAIN = 2 / 3
        self.offset = 1
        self.multiplier = 1

    def getreading(self):
        if self.test:

            import random
            return random.randint(0,50)

            # Read the specified ADC channel using the previously set gain value.
        reading = (self.adc.read_adc(0, gain=self.GAIN))
            # Note you can also pass in an optional data_rate parameter that controls
            # the ADC conversion time (in samples/second). Each chip has a different
            # set of allowed data rate values, see datasheet Table 9 config register
            # DR bit values.
            # values[i] = adc.read_adc(i, gain=GAIN, data_rate=128)
            # Each value will be a 12 or 16 bit signed integer value depending on the
            # ADC (ADS1015 = 12-bit, ADS1115 = 16-bit).
        force =   (reading-self.offset)*self.multiplier
        return force

    def put_reading(self):

        self.force_q.put(self.getreading())


"""
fs = ForceSensor()
readings = []

for i in range(100):
    readings.append(fs.getreading())
print(readings)
plt.plot(readings)
plt.show()

"""
