#!/bin/bash
./rtl_sdr-receiver.py > >(tee output.log) 2> >(tee stderr.log >&2) | grep System: