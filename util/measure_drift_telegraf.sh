#!/bin/bash
CellSearch  -s 7315e5 -e 7315e5 -p 10 2>&1 | grep 'Device index' | awk '{print $3, $9}' | tr -d ':]' | ( while read i s
do
	/opt/radiocapture-motorola/util/measure_drift_telegraf_thread.sh $i $s &
done
wait
)
