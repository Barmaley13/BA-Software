"""
Function to control LED B on E10
LED B located next to ethernet plug
(or LED on Raspberry Pi 3)
"""

### INCLUDES ###
import os

from py_knife import platforms

if platforms.PLATFORM == platforms.RASPBERRY_PI:
    import RPi.GPIO as GPIO


### CONSTANTS ###
GREEN_LED = 'green'
RED_LED = 'red'
BUTTON = 'gpio9260'

if platforms.PLATFORM == platforms.RASPBERRY_PI:
    GREEN_LED = 29
    RED_LED = 31
    BUTTON = 37

## Globals ##
rpi3_init = False


### FUNCTIONS ###    
## Init Raspberry Pi ##
def __init_rpi3_leds():
    """ Initializes RPi3 LEDs """
    global rpi3_init

    if not rpi3_init:
        rpi3_init = True

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(GREEN_LED, GPIO.OUT)
        GPIO.setup(RED_LED, GPIO.OUT)
        GPIO.setup(BUTTON, GPIO.IN)


def __drive_e10_led(led_color, led_state):
    """ Drive Synapse E10 LED """
    os.system("echo " + str(int(led_state)) + " >> /sys/class/leds/" + led_color + "led/brightness")


def __drive_rpi3_led(led_color, led_state):
    """ Drive Raspberry Pi LED """
    __init_rpi3_leds()

    if led_state:
        led_state = GPIO.HIGH
    else:
        led_state = GPIO.LOW

    GPIO.output(led_color, led_state)


def __drive_led(*args, **kwargs):
    """ Generic drive LED function """
    if platforms.PLATFORM == platforms.SYNAPSE_E10:
        __drive_e10_led(*args, **kwargs)

    if platforms.PLATFORM == platforms.RASPBERRY_PI:
        __drive_rpi3_led(*args, **kwargs)


def off():
    """ Turn led off """
    __drive_led(GREEN_LED, False)
    __drive_led(RED_LED, False)


def green():
    """ Turn led green """
    __drive_led(GREEN_LED, True)
    __drive_led(RED_LED, False)


def red():
    """ Turn led red """
    __drive_led(GREEN_LED, False)
    __drive_led(RED_LED, True)


def yellow():
    """ Turn led yellow """
    __drive_led(GREEN_LED, True)
    __drive_led(RED_LED, True)


def button():
    """ Returns state of the E10 button. True - pressed, False - released """
    button_state = False

    if platforms.PLATFORM == platforms.SYNAPSE_E10:
        button_state = not bool(os.system("/usr/bin/" + BUTTON + " ?PB10"))

    if platforms.PLATFORM == platforms.RASPBERRY_PI:
        __init_rpi3_leds()
        button_state = not GPIO.input(BUTTON)

    return button_state
