# Stepper
A stepper motor control app (api and GUI) for BioReactors. Uses DRV 8833 as driver.

# Usage
Run GUI.py and it does the rest :)

# Features
* Perform Experiment
    * Move the motor with a given amplitude and frequency
    * Types of movement:
        * Triangle (Linear)
        * Sinus
    * Wait in between the cycles with a given waiting time
    * Initialize the given starting force

* GUI

    * Adjust the experiment with starting parameters
    * Motor Configuration
    * Live Graphs of motor position and force sensor reading

# Files
* GUI.py
    - Starts the GUI
    - Configures Motor and Experiment and saves the config file
    - Runs the experiment
* experiment.py

    * Starts the experiment from with the configurations from the config file

* motor.py

    * moves the motor and reads the force sensor
* GPIO.py

    * controls the GPIO signals to the DRV8833
* plot.py

    * plots  the graphs for the experiment view

* tools.py, constants.py
    * name says it all

# TODO
dont delete before testing!

* zu hause
- [x] make an experiment window
    - [ ] graphs with matplotlib backend
- [ ] GUI experiment window should show graphs
- [ ] Starting Speed should be read by experiment.py
- [ ] Manual movement Speed should be read by motor.py
