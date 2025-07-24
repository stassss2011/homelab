# -*- coding: utf-8 -*-

import time
import logging
import math
import os
import sys

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_EMC2301 import waveshare_EMC2301

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize fan controller
fan_controller = waveshare_EMC2301.EMC2301()

# Temperature thresholds (C)
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
LOW_TEMP_DURATION = 30  # seconds
VERY_HIGH_TEMP_DURATION = 10  # seconds
CHECK_INTERVAL = 5  # seconds

def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.readline().strip()) / 1000.0
    except Exception as e:
        logger.error(f"Error reading CPU temperature: {e}")
        return None

def get_nvme_temperature():
    try:
        with open("/sys/class/nvme/nvme0/hwmon0/temp1_input") as f:
            return int(f.readline().strip()) / 1000.0
    except Exception as e:
        logger.error(f"Error reading NVMe temperature: {e}")
        return None

def control_fan_speed(speed):
    try:
        fan_controller.EMC2301_Directspeedcontrol(int(speed))
    except Exception as e:
        logger.error(f"Error setting fan speed: {e}")

def calculate_dynamic_speed(temp):
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
    cpu_temp = get_cpu_temperature()
    nvme_temp = get_nvme_temperature()

    temperatures = [t for t in [cpu_temp, nvme_temp] if t is not None]
    if not temperatures:
        return None

    adjusted_nvme_temp = nvme_temp + NVME_TEMP_OFFSET if nvme_temp else None
    effective_temp = max([t for t in [cpu_temp, adjusted_nvme_temp] if t is not None])

    return effective_temp

def decide_fan_speed(temp, current_speed, low_temp_start, very_high_temp_start):
    now = time.time()

    if temp >= VERY_HIGH_TEMP_THRESHOLD:
        very_high_temp_start = very_high_temp_start or now
        if now - very_high_temp_start > VERY_HIGH_TEMP_DURATION:
            return FAN_MAX, None, very_high_temp_start

    elif HIGH_TEMP_THRESHOLD <= temp < VERY_HIGH_TEMP_THRESHOLD:
        return calculate_dynamic_speed(temp), None, None

    elif temp < LOW_TEMP_THRESHOLD:
        low_temp_start = low_temp_start or now
        if now - low_temp_start > LOW_TEMP_DURATION:
            return FAN_OFF, low_temp_start, None

    return current_speed, low_temp_start, very_high_temp_start


def main():
    low_temp_start = None
    very_high_temp_start = None
    current_fan_speed = FAN_OFF
    control_fan_speed(current_fan_speed)

    try:
        while True:
            temperature = get_effective_temperature()
            if temperature is None:
                time.sleep(CHECK_INTERVAL)
                continue

            new_speed, low_temp_start, very_high_temp_start = decide_fan_speed(
                temperature, current_fan_speed, low_temp_start, very_high_temp_start
            )

            if new_speed != current_fan_speed:
                logger.info(f"Fan speed set to {new_speed} (was {current_fan_speed}), Effective temp: {temperature}C")
                control_fan_speed(new_speed)
                current_fan_speed = new_speed

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