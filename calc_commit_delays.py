import glob
import sys
import pandas as pd
import os
import pickle
from collections import defaultdict
from math import ceil
import numpy as np
import file_utils
import plot_utils

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#dump data to file
def dump_data(data, filename):

	#save dictionary chunk to file
	pik = (filename)
	with open(pik, "wb") as f:
		pickle.dump(data, f)
#end dump_data

#--- MAIN EXECUTION BEGINS HERE---#

BIN_SIZE = 0.5			#bin size in hours (0.5 for half hours, 0.25 for quarter hours)

bins = defaultdict(int)

#get list of user commit files to process
files = glob.glob('data_files/user_commits/*')
print("Processing", len(files), "user commit files")

commit_count = 0

#process each file one at a time
for file in files:
	print("Processing", file)

	user_commits = load_pickle(file)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		prev = -1	#time of this user's previous commit

		commit_count += len(commits)

		#loop all commits made by this user
		for c in commits:

			#compute delay between this commit and the previous (if previous commit exists)
			if prev != -1:
				delay = c['time'] - prev
			else:
				delay = None

			#make sure commits in sorted order, quit if not
			if delay != None and delay < 0:
				print("Fail, commits not in time-order")
				exit(0)

			#process delay if valid
			if delay != None:

				#simultaneous commits? (no delay) -> special 0-hour bin
				if prev == c['time']:
					bins[0] += 1
				#valid delay, convert to hours add to correct bin counter
				else:
					bins[ceil(delay / (BIN_SIZE * 3600)) * BIN_SIZE] += 1		

			prev = c['time']	#update prev for next commit

print("Processed", commit_count, "commits")

#save frequency counts as csv file
file_utils.dump_dict_csv(bins, ['delay(hours)', 'freq'], "results/commit_delay_analysis/delay_freq_%s.csv" % BIN_SIZE)

#plot as well for quick look at results
#all data
plot_utils.plot_dict_data(bins, "delay (hours)", "frequency", "Commit Delay Distribution", filename = "results/commit_delay_analysis/delay_freq_%s.png" % BIN_SIZE, log_scale_y = True)
#narrowed range, not log-scale
plot_utils.plot_dict_data(bins, "delay (hours)", "frequency", "Commit Delay Distribution", filename = "results/commit_delay_analysis/delay_freq_narrow_%s.png" % BIN_SIZE, x_min = 4, x_max = 16)

print("Results saved and plotted as results/commit_delay_analysis/delay_freq_%s" % BIN_SIZE)