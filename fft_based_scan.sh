for i in 0 1 2 3 4 5 6 7 8 9
do
	python3 fft_vector.py -i $i
	python3 fft_peak_detection.py -i $i
done
