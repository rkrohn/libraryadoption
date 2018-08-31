#!/bin/bash

#STR="$(date +"%F_%T")" && time python3 classify_by_day.py "predict_tests/results_by_day_$STR" CUPLS > "predict_tests/test_by_day_$STR.log" &

#loop featuresets
for features in UPLS CPLS CULS CUPS C U P L S; do
	STR=""$features"_$(date +"%F_%T")"
	echo $(date +"%F_%T") running $features

	time python3 classify_by_day.py "predict_tests/results_by_day_$STR" $features > "predict_tests/test_by_day_$STR.log"
	sleep 30
done 