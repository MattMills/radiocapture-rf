for i in $(ls -1 /tmp/rx_source_* | grep -Eo '[0-9]*')
do
	python3 fft_vector.py -i $i
	python3 fft_peak_detection.py -i $i
done
