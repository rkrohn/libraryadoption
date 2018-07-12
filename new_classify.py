#new version of the classifier training/testing program for the new_event_features (see updated_feature_vector.txt for notes on features)

import pickle
import numpy as np
from sklearn import linear_model
from sklearn import preprocessing as pp
from sklearn import metrics
import itertools as it
import sys

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#load all data for specified year range (inclusive) and return as a single events list and separate labels list
def load_year_range(start, end=-1, month_start=1, month_end=12):
	all_events = []
	all_labels = []

	if end == -1:
		end = start

	for year in range(start, end+1):
		print("Loading events for", str(year) + ", months " + str(month_start) + "-" + str(month_end) if month_start != month_end else str(year) + ", month " + str(month_start))

		#load all requested months of data
		for month in range(month_start, month_end+1):
			#read raw (list-format) data for this month
			events = load_pickle("data_files/new_event_features/%s/%s_events.pkl" % (year, month))
			labels = load_pickle("data_files/new_event_features/%s/%s_labels.pkl" % (year, month))

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

if len(sys.argv) < 2:
	print("Requires command line argument for results filename (without extension). Exiting")
	exit(0)

results_file = sys.argv[1]

#set training and testing years here
training_start = 2004
training_end = 2005		#this year will be included in training
training_month_start = 1
training_month_end = 12
testing_year = 2006		#single year for testing, and for now only the first month
testing_month_start = 1
testing_month_end = 1

#set number of iterations for training
num_iter = 50

#set your configuration choices here - dictionary with list as value
#loops will test all combinations of these arguments
config_choices = {'loss': ['squared_hinge'], 'penalty': ['none', 'l2', 'l1', 'elasticnet'], 'shuffle': [True], 'fit_intercept': [True, False]}

#select the features (columns) to include in training (ranges include first, exclude last, list multiple if desired)
features = "UPL"	#U = user, P = pair (user-package), L = library, S = stackoverflow

feature_idx = []	#start with no features, add on what you want
if 'C' in features:
	feature_idx.extend(range(4, 7))		#commit features
if 'U' in features:
	feature_idx.extend(range(7, 19))	#user features	
if 'P' in features:
	feature_idx.extend(range(23, 29))	#match (user/package) features
if 'L' in features:
	feature_idx.extend(range(29, 40))	#package/library features
if 'S' in features:
	feature_idx.extend(range(40, 44))	#StackOverflow features

feature_idx = np.array(feature_idx)	#convert to numpy array
print("Using features", feature_idx, "\n")

#build list of combinations to pass as arguments to classifier configuration
config_keys = sorted(config_choices)
#combos = list(it.product(*(config_choices[key] for key in config_keys)))
combos = [(True, 'squared_hinge', 'l2', True), (False, 'squared_hinge', 'l1', True)]	#hardcode for now
print("Testing", len(combos), "classifier configurations\n")

#load all training data, convert events to np array for easier indexing
print("TRAINING DATA:")
training_events_raw, training_labels_raw = load_year_range(training_start, training_end, month_start = training_month_start, month_end = training_month_end)
training_events_raw = np.array(training_events_raw)

#convert training data to np arrays
training_events = training_events_raw[:,feature_idx].astype(np.float32) 	#select desired features, convert to float
training_labels = np.asarray(training_labels_raw, dtype=np.float32)

#replace any nan values with 0
replace_nan(training_events)

#normalize all training data (including training normalizer)
print("Using MinMaxScaler for normalization")
scaler = pp.MinMaxScaler()
training_events = scaler.fit_transform(training_events)

print("read", training_events.shape[0], "import training events with", training_events.shape[1], "features")
print("   ", int(sum(training_labels)), "events are adoptions\n")

#read testing data, convert events to np array for easier indexing
print("TESTING DATA:")
testing_events_raw, testing_labels_raw = load_year_range(testing_year, month_start=testing_month_start, month_end=testing_month_end)
testing_events_raw = np.array(testing_events_raw)

#convert testing data to np array
testing_events = testing_events_raw[:,feature_idx].astype(np.float32)		#select desired features, convert to float
testing_labels = np.asarray(testing_labels_raw, dtype=np.float32)

#replace any nan values with 0
replace_nan(testing_events)

#normalize the testing data, using same scaler as generated by training data
testing_events = scaler.transform(testing_events)

print("read", testing_events.shape[0], "testing events with", testing_events.shape[1], "features")
print("   ", int(sum(testing_labels)), "events are adoptions\n")
num_features = testing_events.shape[1]

#build list of column headers - will dump data to csv
results = []
results.append(["test#", "training_year_first", "training_year_last", "training_month_first", "training_month_last", "testing_year", "testing_month_first", "testing_month_last", "features", "penalty", "fit_intercept", "loss", "shuffle", "num_iter", "true_pos", "true_neg", "false_pos", "false_neg", "precision", "recall", "f1-score",	"AUROC"])


#run multiple classifier tests one after the other - both repeated runs and different configurations
#configuration combos generated above

#for each configuration combo, run the classifier!
for c in range(len(combos)):
	combo = combos[c]
	kw = {}
	for i in range(0, len(config_keys)):
		kw[config_keys[i]] = combo[i]
		
	print("\nTEST", c, kw)

	#train the classifier
	print("Training classifier...")
	clf = linear_model.SGDClassifier(n_iter=num_iter, **kw)
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

	#F1-score, AUROC, precision, and recall
	f_score = metrics.f1_score(testing_labels, predicted_labels)	
	auroc = metrics.roc_auc_score(testing_labels, predicted_labels)
	precision = metrics.precision_score(testing_labels, predicted_labels)
	recall = metrics.recall_score(testing_labels, predicted_labels)

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
	print("precision:", precision)
	print("recall:", recall)
	print("F-1 score:", f_score)
	print("AUROC score:", auroc)

	#append results for this run to overall results data
	results.append([c, training_start, training_end, training_month_start, training_month_end, testing_year, testing_month_start, testing_month_end, features, kw['penalty'], kw['fit_intercept'], kw['loss'], kw['shuffle'], num_iter, true_pos, true_neg, false_pos, false_neg, precision, recall, f_score, auroc])

#save results from all runs to output file, base name specified by command line arg
np.savetxt((results_file + ".csv"), np.array(results), delimiter=", ", fmt="%s")
print("\nAll results saved to", results_file + ".csv")


