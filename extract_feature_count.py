import glob
import re
import pandas as pd

#--- MAIN EXECUTION BEGINS HERE---#

#get list of files to combine
files = glob.glob('predict_tests/results*')
print(files[0])

#process all files
#extract date stamp portion of filename: predict_tests/results_2018-07-07_10:49:14.csv -> 2018-07-07_10:49:14
#and build name of corresponding test log file: 2018-07-07_10:49:14 -> predict_tests/test_2018-07-07_10:49:14.log
for file in files:
	log = "predict_tests/test_" + file[22:-4] + ".log"
	print(log)

	#find matching line in log file
	res = [match[0] for match in [re.findall(r'read [0-9]* testing events with [0-9]* features', line) for line in open(log)] if len(match) != 0][0]

	#extract # of features used in those tests
	feature_count = [int(s) for s in res.split(' ') if s.isdigit()][1]

	#read in corresponding results file
	data = pd.read_csv(file)

	#add new column containing feature count
	data.insert(8, "num_features", feature_count)

	#save modified file
	data.to_csv(file)