import pickle
import numpy as np
from sklearn import linear_model
from sklearn import preprocessing as pp
from sklearn import metrics
import itertools as it

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#load all data for specified year range (inclusive) and return as a single events list and separate labels list
def load_year_range(start, end=-1, months=12):
	all_events = []
	all_labels = []

	if end == -1:
		end = start

	for year in range(start, end+1):
		print("Loading events for", year)

		#load all requested months of data
		for month in range(1, 1+months):
			#read raw (list-format) data for this month
			events = load_pickle("data_files/event_features/%s/%s_events.pkl" % (year, month))
			labels = load_pickle("data_files/event_features/%s/%s_labels.pkl" % (year, month))

			#append to all data
			all_events.extend(events)
			all_labels.extend(labels)

	return all_events, all_labels
#end load_year_range

#given an np array, replace any nan values with value
def replace_nan(data, value = 0):
	print("Replacing nan with", value)
	data[np.isnan(data)] = value
#end replace_nan

#--- MAIN EXECUTION BEGINS HERE---#

#set training and testing years here
training_start = 1993
training_end = 2014		#this year will be included in training
testing_year = 2015		#single year for testing, and for now only the first month

#set your configuration choices here - dictionary with list as value
#loops will test all combinations of these arguments
config_choices = {'loss': ['squared_hinge'], 'penalty': ['none', 'l2', 'l1', 'elasticnet'], 'shuffle': [True, False], 'fit_intercept': [True, False]}

#build list of combinations to pass as arguments to classifier configuration
config_keys = sorted(config_choices)
combos = list(it.product(*(config_choices[key] for key in config_keys)))
print("Testing", len(combos), "classifier configurations\n")

#load all training data
training_events_raw, training_labels_raw = load_year_range(training_start, training_end)

#convert training data to np arrays
training_events = np.asarray(training_events_raw, dtype=np.float32)
training_labels = np.asarray(training_labels_raw, dtype=np.float32)
print("read", training_events.shape[0], "import training events with", training_events.shape[1], "features")
print("   ", int(sum(training_labels)), "events are adoptions\n")

#replace any nan values with 0
replace_nan(training_events)

#normalize all training data (including training normalizer)
scaler = pp.MinMaxScaler()
training_events = scaler.fit_transform(training_events)

#read testing data
testing_events_raw, testing_labels_raw = load_year_range(testing_year, months=1)

#convert testing data to np array
testing_events = np.asarray(testing_events_raw, dtype=np.float32)
testing_labels = np.asarray(testing_labels_raw, dtype=np.float32)
print("read", testing_events.shape[0], "testing events with", testing_events.shape[1], "features\n")

#replace any nan values with 0
replace_nan(testing_events)

#normalize the testing data, using same scaler as generated by training data
testing_events = scaler.transform(testing_events)

#run multiple classifier tests one after the other - both repeated runs and different configurations
#configuration combos generated above

#for each configuration combo, run the classifier!
for c in range(len(combos)):
	combo = combos[c]
	kw = {}
	for i in range(0, len(config_keys)):
		kw[config_keys[i]] = combo[i]
		
	print("\nTest", c, kw)

	#train the classifier
	print("Training classifier...")
	clf = linear_model.SGDClassifier(n_iter=50, **kw)
	print(clf.fit(training_events, training_labels), "\n")
	#clf.fit(training_events, training_labels)

	print("\ncoefficients:", clf.coef_)
	print("intercept:", clf.intercept_, "\n")

	#predict on the testing events
	predicted_labels = clf.predict(testing_events)

	#look for adoptions, correctly predicted or not

	#how many adoptions in real labels vs predicted?
	print(int(sum(testing_labels)), "adoption events in", len(testing_labels), "import events")
	print("predicted", int(sum(predicted_labels)), "adoptions")

	#F1-score
	f_score = metrics.f1_score(testing_labels, predicted_labels)	

	#AUROC measure
	auroc = metrics.roc_auc_score(testing_labels, predicted_labels)

	#of the predicted adoptions, how many were correct vs false positives?
	true_neg = 0
	true_pos = 0
	false_neg = 0
	false_pos = 0
	for i in range(0, len(predicted_labels)):
		if testing_labels[i] == 0 and predicted_labels[i] == 0:
			true_neg += 1
		elif testing_labels[i] == 0 and predicted_labels[i] == 1:
			false_pos += 1
		elif testing_labels[i] == 1 and predicted_labels[i] == 0:
			false_neg += 1
		else:
			true_pos += 1

	#print all metrics
	print("\ntrue pos:", true_pos)
	print("true neg:", true_neg)
	print("false pos:", false_pos)
	print("false neg:", false_neg, "\n")
	print("F-1 score:", f_score)
	print("AUROC score:", auroc)

