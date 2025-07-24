# -*- coding: utf-8 -*-

import time
import subprocess
import logging
import math
import os
import sys
import json

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_EMC2301 import waveshare_EMC2301

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize fan controller
fan_controller = waveshare_EMC2301.EMC2301()

# Temperature thresholds (in Celsius)
LOW_TEMP_THRESHOLD = 45.0
HIGH_TEMP_THRESHOLD = 55.0
VERY_HIGH_TEMP_THRESHOLD = 75.0

# NVMe Temperature offset
NVME_TEMP_OFFSET = 5

# Fan speed constants
FAN_OFF = 0
FAN_MIN = 100
FAN_MAX = 255

# Timing constants
LOW_TEMP_DURATION = 30  # Seconds below LOW_TEMP_THRESHOLD to turn off fan
VERY_HIGH_TEMP_DURATION = 10  # Seconds above VERY_HIGH_TEMP_THRESHOLD to force max speed
CHECK_INTERVAL = 5  # Temperature check interval in seconds

def get_temperature():
    """Reads the CPU temperature."""
    try:
        temp_output = subprocess.check_output(['/usr/bin/vcgencmd', 'measure_temp']).decode('utf-8')
        return float(temp_output.replace("temp=", "").replace("'C", "").strip())
    except Exception as e:
        logger.error(f"Error reading CPU temperature: {e}")
        return None

def get_nvme_temperature():
    """Reads the NVMe temperature."""
    try:
        output = subprocess.check_output(['nvme', 'smart-log', '/dev/nvme0n1', '--output-format', 'json']).decode('utf-8')
        data = json.loads(output)
        return math.ceil(data["temperature"] - 273.15)  # Convert from Kelvin to Celsius
    except Exception as e:
        logger.error(f"Error reading NVMe temperature: {e}")
        return None

def control_fan_speed(speed):
    """Sets the fan speed."""
    try:
        fan_controller.EMC2301_Directspeedcontrol(int(speed))
        logger.info(f"Fan speed set to {speed}")
    except Exception as e:
        logger.error(f"Error setting fan speed: {e}")

def calculate_dynamic_speed(temp):
    """
    Calculates dynamic fan speed based on temperature.
    Adjusts speed non-linearly for a smoother experience.
    """
    temp_range = VERY_HIGH_TEMP_THRESHOLD - HIGH_TEMP_THRESHOLD
    if temp >= VERY_HIGH_TEMP_THRESHOLD:
        return FAN_MAX
    elif temp >= HIGH_TEMP_THRESHOLD:
        # Calculate fan speed between FAN_MIN and FAN_MAX
        temp_factor = (temp - HIGH_TEMP_THRESHOLD) / temp_range
        # Apply a non-linear scaling to make adjustments smoother
        speed = FAN_MIN + (temp_factor ** 1.5) * (FAN_MAX - FAN_MIN)
        return min(max(FAN_MIN, speed), FAN_MAX)
    else:
        return FAN_MIN

def get_effective_temperature():
    cpu_temp = get_temperature()
    nvme_temp = get_nvme_temperature()
    

    temperatures = [t for t in [cpu_temp, nvme_temp] if t is not None]
    if not temperatures:
        return None

    adjusted_nvme_temp = nvme_temp + NVME_TEMP_OFFSET if nvme_temp else None
    effective_temp = max([t for t in [cpu_temp, adjusted_nvme_temp] if t is not None])

    #logger.info(f"CPU temperature: {cpu_temp}C, NVME temperature: {nvme_temp}C, Effective temperature: {effective_temp}C")

    return effective_temp

def main():
    low_temp_start = None
    very_high_temp_start = None
    current_fan_speed = FAN_OFF
    control_fan_speed(FAN_OFF)

    try:
        while True:
            temperature = get_effective_temperature()
            if temperature is None:
                time.sleep(CHECK_INTERVAL)
                continue

            if temperature >= VERY_HIGH_TEMP_THRESHOLD:
                if very_high_temp_start is None:
                    very_high_temp_start = time.time()
                elif time.time() - very_high_temp_start > VERY_HIGH_TEMP_DURATION:
                    if current_fan_speed != FAN_MAX:
                        control_fan_speed(FAN_MAX)
                        current_fan_speed = FAN_MAX
                low_temp_start = None
            else:
                very_high_temp_start = None

            if HIGH_TEMP_THRESHOLD <= temperature < VERY_HIGH_TEMP_THRESHOLD:
                new_speed = calculate_dynamic_speed(temperature)
                if current_fan_speed != new_speed:
                    control_fan_speed(new_speed)
                    current_fan_speed = new_speed
                low_temp_start = None

            if temperature < LOW_TEMP_THRESHOLD:
                if low_temp_start is None:
                    low_temp_start = time.time()
                elif time.time() - low_temp_start > LOW_TEMP_DURATION:
                    if current_fan_speed != FAN_OFF:
                        control_fan_speed(FAN_OFF)
                        current_fan_speed = FAN_OFF
                very_high_temp_start = None

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logger.info('Service interrupted by user')
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Shutting down fan controller.")
        control_fan_speed(FAN_OFF)

if __name__ == "__main__":
    main()
