#!/bin/bash

#STR="$(date +"%F_%T")" && time python3 classify_by_day.py "predict_tests/results_by_day_$STR" CUPLS > "predict_tests/test_by_day_$STR.log" &


#loop featuresets
#for features in CUPLS CUPL UPLS CPLS CULS CUPS C U P L S CUP CUL CUS CPL CPS CLS UPL UPS ULS PLS CU CP CL CS UP UL US PL PS LS; do
#	STR=""$features"_$(date +"%F_%T")"
#	echo $(date +"%F_%T") running $features
#
#	time python3 classify_by_day.py "predict_tests/results_by_day_$STR" $features > "predict_tests/test_by_day_$STR.log"
#	sleep 30
#done


#loop featuresets in a few chunks so we don't overload the server
for features in CUPLS CUPL UPLS CPLS CULS; do
	STR=""$features"_$(date +"%F_%T")"
	echo $(date +"%F_%T") running $features

	time python3 new_classify.py "predict_tests/results_Jan18_$STR" $features > "predict_tests/test_Jan18_$STR.log" &
	sleep 1
done
wait		#wait for those to finish before we spin up more

#loop featuresets in a few chunks so we don't overload the server
for features in CUPS C U P L S; do
	STR=""$features"_$(date +"%F_%T")"
	echo $(date +"%F_%T") running $features

	time python3 new_classify.py "predict_tests/results_Jan18_$STR" $features > "predict_tests/test_Jan18_$STR.log" &
	sleep 1
done
wait		#wait for those to finish before we spin up more

#loop featuresets in a few chunks so we don't overload the server
for features in CUP CUL CUS CPL CPS; do
	STR=""$features"_$(date +"%F_%T")"
	echo $(date +"%F_%T") running $features

	time python3 new_classify.py "predict_tests/results_Jan18_$STR" $features > "predict_tests/test_Jan18_$STR.log" &
	sleep 1
done
wait		#wait for those to finish before we spin up more

#loop featuresets in a few chunks so we don't overload the server
for features in CLS UPL UPS ULS PLS; do
	STR=""$features"_$(date +"%F_%T")"
	echo $(date +"%F_%T") running $features

	time python3 new_classify.py "predict_tests/results_Jan18_$STR" $features > "predict_tests/test_Jan18_$STR.log" &
	sleep 1
done
wait		#wait for those to finish before we spin up more

#loop featuresets in a few chunks so we don't overload the server
for features in CU CP CL CS UP; do
	STR=""$features"_$(date +"%F_%T")"
	echo $(date +"%F_%T") running $features

	time python3 new_classify.py "predict_tests/results_Jan18_$STR" $features > "predict_tests/test_Jan18_$STR.log" &
	sleep 1
done
wait		#wait for those to finish before we spin up more

#loop featuresets in a few chunks so we don't overload the server
for features in UL US PL PS LS; do
	STR=""$features"_$(date +"%F_%T")"
	echo $(date +"%F_%T") running $features

	time python3 new_classify.py "predict_tests/results_Jan18_$STR" $features > "predict_tests/test_Jan18_$STR.log" &
	sleep 1
done
