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

#loads and processes data for specified time range and featureset
def load_data(start, end, month_start, month_end, remove_repeat_usages, downsample_ratio, feature_idx, scaler = -1):

	#load all data, convert events to np array for easier indexing
	events_raw, labels_raw = load_year_range(start, end, month_start, month_end)
	events_raw = np.array(events_raw)
	labels_raw = np.array(labels_raw)

	#print some counts (for humans)
	print("Read", events_raw.shape[0], "events with", events_raw.shape[1], "features")
	print("   ", int(sum(labels_raw)), "events are adoptions")

	#filter out repeat usages if flag is set
	if remove_repeat_usages:
		rows = np.where(events_raw[:,22] == 0)[0]		#rows where user hasn't committed package before
		print("Filtering from", len(events_raw), "events to", len(rows), "events")
		events_raw = events_raw[rows]
		labels_raw = labels_raw[rows]

	#downsample negative events in training data only according to specified ratio
	if downsample_ratio is not None and scaler == -1:
		print("Downsampling neg:pos ratio to", str(downsample_ratio) + ":1")

		#grab row indexes for positive events and negative events separately
		pos_rows = np.where(labels_raw == 1)[0]
		neg_rows = np.where(labels_raw == 0)[0]
		
		#select ratio*len(pos) negative row indices
		sampled_neg_rows = np.random.choice(neg_rows, downsample_ratio*len(pos_rows), replace=False)

		rows = np.concatenate([pos_rows, sampled_neg_rows])	#merge row lists

		#filter events and labels to only those included in sample
		events_raw = events_raw[rows]
		labels_raw = labels_raw[rows]

	elif scaler == -1:
		print("No downsampling")

	#convert data to np arrays of correct type
	events = events_raw[:,feature_idx].astype(np.float32) 	#select desired features, convert to float
	labels = np.asarray(labels_raw, dtype=np.float32)

	#replace any nan values with 0
	replace_nan(events)

	#no provided scaler (training data): normalize all data (including training normalizer)
	if scaler == -1:
		print("Using MinMaxScaler for normalization")
		training_scaler = pp.MinMaxScaler()
		events = training_scaler.fit_transform(events)
	#given a scaler (testing data): normalize data with pre-trained scaler
	else:
		events = scaler.transform(events)

	#print some counts (for humans)
	print("Final data contains", events.shape[0], "events with", events.shape[1], "features")
	print("   ", int(sum(labels)), "events are adoptions\n")

	#return events and labels
	if scaler == -1:
		return events, labels, training_scaler
	else:
		return events, labels
#end load_data

#given an np array, replace any nan values with value
def replace_nan(data, value = 0):
	print("Replacing nan with", value)
	data[np.isnan(data)] = value
#end replace_nan

#--- MAIN EXECUTION BEGINS HERE---#

if len(sys.argv) < 3:
	print("Requires command line argument for results filename (without extension) and feature classes to include (CUPLS). Exiting")
	exit(0)

results_file = sys.argv[1]
features = sys.argv[2]

#set training and testing years here
training_start = 2011
training_end = 2011		#this year will be included in training
training_month_start = 12
training_month_end = 12
testing_year = 2012		#single year for testing, and for now only the first month
testing_month_start = 1
testing_month_end = 1

#set number of iterations for training
num_iter = 50

remove_repeat_usages = True	#if flag is true, remove user-package events where user has already used this library before

downsample_ratio = 4		#if None, no downsampling of negative events
				#if a whole number X, sample to have X negative events for each positive event

#set your configuration choices here - dictionary with list as value
#loops will test all combinations of these arguments
config_choices = {'loss': ['squared_hinge'], 'penalty': ['none', 'l2', 'l1', 'elasticnet'], 'shuffle': [True], 'fit_intercept': [True, False]}

#select the features (columns) to include in training (ranges include first, exclude last, list multiple if desired)
#features = "CUPLS"	#U = user, P = pair (user-package), L = library, S = stackoverflow, C = commit
#features selected via command line arg

feature_idx = []	#start with no features, add on what you want
if 'C' in features:
	feature_idx.extend(range(4, 7))		#commit features
if 'U' in features:
	feature_idx.extend(range(7, 19))	#user features	
if 'P' in features:
	feature_idx.extend(range(23, 29))	#pair (user/library) features
if 'L' in features:
	feature_idx.extend(range(29, 40))	#library features
if 'S' in features:
	feature_idx.extend(range(40, 44))	#StackOverflow features

feature_idx = np.array(feature_idx)	#convert to numpy array
print("Using features", feature_idx, "\n")

#build list of combinations to pass as arguments to classifier configuration
config_keys = sorted(config_choices)
combos = list(it.product(*(config_choices[key] for key in config_keys)))
print("Testing", len(combos), "classifier configurations\n")

#load all training data as np array
print("TRAINING DATA:")
training_events, training_labels, scaler = load_data(training_start, training_end, training_month_start, training_month_end, remove_repeat_usages, downsample_ratio, feature_idx)

#load testing data as np array
print("TESTING DATA:")
testing_events, testing_labels = load_data(testing_year, -1, testing_month_start, testing_month_end, remove_repeat_usages, downsample_ratio, feature_idx, scaler)

num_features = testing_events.shape[1]		#grab number of features for csv output

#build list of column headers - will dump data to csv
results = []
results.append(["test#", "filter_repeat", "training_year_first", "training_year_last", "training_month_first", "training_month_last", "testing_year", "testing_month_first", "testing_month_last", "features", "penalty", "fit_intercept", "loss", "shuffle", "num_iter", "true_pos", "true_neg", "false_pos", "false_neg", "precision", "recall", "f1-score",	"AUROC"])

#run multiple classifier tests one after the other - both repeated runs and different configurations
#configuration combos generated above
#wrap all this in an outer loop, so we can more easily run 5 (or more) of the same test, and save I/O time

#repeated runs of same configuration
for i in range(0, 5):
	print("\nRUN", i)

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
		results.append([c, remove_repeat_usages, training_start, training_end, training_month_start, training_month_end, testing_year, testing_month_start, testing_month_end, features, kw['penalty'], kw['fit_intercept'], kw['loss'], kw['shuffle'], num_iter, true_pos, true_neg, false_pos, false_neg, precision, recall, f_score, auroc])
		
	#end configuration for
#end repeated runs for

#save results from all runs to output file, base name specified by command line arg
np.savetxt((results_file + ".csv"), np.array(results), delimiter=",", fmt="%s")
print("\nAll results saved to", results_file + ".csv")


