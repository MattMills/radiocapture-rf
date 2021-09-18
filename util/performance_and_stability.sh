#!/bin/bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
echo 0 | sudo tee > /sys/module/usbcore/parameters/usbfs_memory_mb
