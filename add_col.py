import glob
import sys
import pandas as pd
import os

#--- MAIN EXECUTION BEGINS HERE---#

#get list of files to combine
files = glob.glob('predict_tests/results*')
print("Updating", len(files), "files")

for file in files:
	csv_input = pd.read_csv(file)
	if "downsample_ratio" not in csv_input.columns:
		csv_input.insert(2, "downsample_ratio", -1)
		csv_input.to_csv(file, index=False)
