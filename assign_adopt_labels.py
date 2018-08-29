import json
from datetime import datetime, timedelta
import random as r
from collections import deque
import pickle
import os.path
import glob

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#dump all currently cached data (for a single month) to file
def dump_labels(labels, data_month, data_year):
	#no data yet, skip
	if data_year == -1:
		return

	#make sure directory for this year exists
	if os.path.isdir("data_files/new_event_features/%s" % data_year) == False:
		os.makedirs("data_files/new_event_features/%s" % data_year)

	#save updated labels to file
	pik = ("data_files/new_event_features/%s/%s_updated_labels.pkl" % (data_year, data_month))
	with open(pik, "wb") as f:
		pickle.dump(labels, f)	

	print ("   saved labels for %s-%s" % (data_month, data_year))
#end dump_data

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":

	labels = []		#list of labels for current month

	#stream data from sorted json files
	for year in range(1990, 2019):		#read and process 1990 through 2018
		print("PROCESSING", year, ":", end = " ")

		#get list of feature files to process for this year
		files = set(glob.glob('data_files/new_event_features/%s/*events*' % year)) - set(glob.glob('data_files/new_event_features/%s/*empty*' % year))
		print(len(files), "month event files")

		for file in files:
			print("   assigning labels to", file)

			#extract month number from filename
			month = file[35:37]		#digits, plus maybe a trailing underscore
			if month[1] == '_':
				month = month[0]
			month = int(month)

			#load events for this month
			month_events = load_pickle(file)

			#loop all events in this month
			for event in month_events:

				#assign new label
				#adoption: if user committed lib, hasn't committed lib before, and user "seen" lib at least once
				if event[20] == 1 and event[22] == 0 and event[23] > 0:
					labels.append(1)		#1 = adoption
				else:
					labels.append(0)		#0 = not an adoption

			#save month labels
			dump_labels(labels, month, year)

			#clear labels
			labels = []

