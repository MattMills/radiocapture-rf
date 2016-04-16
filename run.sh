#!/bin/bash
./receiver.py > >(tee output.log) 2> >(tee stderr.log >&2) | grep System:
