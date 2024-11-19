# -*- coding: utf-8 -*-

import logging
import os
import sys

from logging.handlers import RotatingFileHandler

# Configure logging with rotation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_EMC2301 import waveshare_EMC2301
# Initialize fan controller
obj = waveshare_EMC2301.EMC2301()

def control_fan_speed(speed):
    """Sets the fan speed."""
    try:
        obj.EMC2301_Directspeedcontrol(speed)
        logger.info(f"Fan speed set to {speed}")
    except Exception as e:
        logger.error(f"Error setting fan speed: {e}")

def main():
    """Main loop to set fan speed from console input."""
    try:
        while True:
            try:
                speed = int(input("Enter fan speed (0-255): "))
                if 0 <= speed <= 255:
                    control_fan_speed(speed)
                else:
                    logger.warning("Please enter a valid speed between 0 and 255.")
            except ValueError:
                logger.warning("Invalid input. Please enter a number between 0 and 255.")
    except KeyboardInterrupt:
        logger.info('Service interrupted by user')
    finally:
        logger.info("Shutting down fan controller.")
        control_fan_speed(0)  # Turn off the fan on exit

if __name__ == "__main__":
    main()
