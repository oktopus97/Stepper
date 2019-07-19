from configparser import ConfigParser
import math


"""
--------------------------------
tools for the delay computation 
used by:motor.py

params:
    
    a = amplitude
    sc=stepcount
    f = frequency [1/s]
    s=steps_per_mm

returns:
    delay [s]
"""

def computeLinearDelay(step_count,frequency):
    
    delay = 1/(step_count*frequency*4)#muss noch halbiert werden, weil das programm zweimal schläft
    return delay

def get_sin_table(steps, frequency):
    sampled_t = []
    delays = []
    step_count = 0
    for i in range(int(steps)+1):

        sampled_t.append(math.asin(step_count/steps)/(2*math.pi*frequency))
        step_count += 1
    
    
    for i in range(1, len(sampled_t)):
        delays.append((sampled_t[i]- sampled_t[i-1])/2)
    return delays
    
    

##config reader


def configreader( *args, category, file):
    
    config = ConfigParser(strict=False)
    
    config.read(file)
    
            
    variables = []
    for variable in args:
        variables.append(config.get(category,variable))
    return variables


#config writer
def configwriter(file, category, featurenames ,*features):##maybe wth conf parser
    config = ConfigParser(strict=False)
    config.read(file)
    
    for i, variable in enumerate(features):
        
        config.set(category,featurenames[i],str(variable))  
    
    with open(file,"w") as f:
        config.write(f,"w")