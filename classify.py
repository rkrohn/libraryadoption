import pickle
import numpy as np
from sklearn import linear_model

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#load all data for specified year range (inclusive) and return as a single events list and separate labels list
def load_year_range(start, end=-1):
	all_events = []
	all_labels = []

	if end == -1:
		end = start

	for year in range(start, end+1):
		print("Loading events for", year)

		#load all months of data
		for month in range(1, 13):
			#read raw (list-format) data for this month
			events = load_pickle("data_files/event_features/%s/%s_events.pkl" % (year, month))
			labels = load_pickle("data_files/event_features/%s/%s_labels.pkl" % (year, month))	

			#append to all data
			all_events.extend(events)
			all_labels.extend(labels)
	
	return all_events, all_labels
#end load_year_range

#given an np array, replace any nan values with value
def replace_nan(data, value = -1):
	data[np.isnan(data)] = value
#end replace_nan

#--- MAIN EXECUTION BEGINS HERE---#

#set training and testing years here
training_start = 1993
training_end = 1993		#this year will be included in training
testing_year = 1994		#single year for testing

#load all training data
training_events_raw, training_labels_raw = load_year_range(training_start, training_end)

#convert training data to np arrays
training_events = np.asarray(training_events_raw, dtype=np.float32)
training_labels = np.asarray(training_labels_raw, dtype=np.float32)
print("read", training_events.shape[0], "training events with", training_events.shape[1], "features\n")

#replace any nan values with -1
replace_nan(training_events)

#train the classifier
clf = linear_model.SGDClassifier(shuffle=True)
print(clf.fit(training_events, training_labels))

print("\ncoefficients:", clf.coef_)
print("intercept:", clf.intercept_, "\n")

#read testing data
testing_events_raw, testing_labels_raw = load_year_range(testing_year)

#convert testing data to np array
testing_events = np.asarray(testing_events_raw, dtype=np.float32)
testing_labels = np.asarray(testing_labels_raw, dtype=np.float32)
print("read", testing_events.shape[0], "testing events with", testing_events.shape[1], "features")

#replace any nan values with -1
replace_nan(testing_events)

#predict on the testing events
predicted_labels = clf.predict(testing_events)

#for now, just print predicted vs actual for the first 25 events
print("\nactual\tpredicted")
for i in range(0, 25):
	print(testing_labels[0], "\t", predicted_labels[0])


