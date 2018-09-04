#new version of the classifier training/testing program for the new_event_features (see updated_feature_vector.txt for notes on features)

import pickle
import numpy as np
from sklearn import linear_model
from sklearn import preprocessing as pp
from sklearn import metrics
import itertools as it
import sys
from calendar import monthrange
import datetime
from datetime import timezone
import random
from datetime import timedelta
from collections import defaultdict

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#load all data for specified date range (inclusive) and return as a single events list and separate labels list
#load data in month-size chunks, starting with month_start-year_start and ending with (inclusive) month_end-year_end
def load_date_range(year_start, year_end, month_start=1, month_end=12):
	all_events = []
	all_labels = []

	print("Loading events from", str(month_start) + "-" + str(year_start), ("through "+ str(month_end) + "-" + str(year_end) if month_start != month_end or year_start != year_end else ""))

	for year in range(year_start, year_end+1):
		print("   Loading events for", str(year), ": ", end = "")

		#set start and end month range for this year
		load_month_start = month_start if year == year_start else 1
		load_month_end = month_end if year == year_end else 12

		#load all requested months of data
		for month in range(load_month_start, load_month_end+1):
			print(month, end=" ")

			#read raw (list-format) data for this month
			events = load_pickle("data_files/new_event_features/%s/%s_events.pkl" % (year, month))
			labels = load_pickle("data_files/new_event_features/%s/%s_labels.pkl" % (year, month))

			#append to all data
			all_events.extend(events)
			all_labels.extend(labels)

		print("")

	return all_events, all_labels
#end load_year_range

#loads and processes data for specified time range and featureset
def load_data(all_events_raw, all_labels_raw, date_start, date_end, downsample_ratio, feature_idx, scaler = -1):

	#load all data, convert events to np array for easier indexing
	#load entire months containing data range we actually want
	events_raw = np.array(all_events_raw)
	labels_raw = np.array(all_labels_raw)

	#filter data to only records within date range
	#start and end dates include correct time - midnight am for start, midnight pm for end - so conver to timestamp for filter
	timestamp_start = int(date_start.replace(tzinfo=timezone.utc).timestamp())
	timestamp_end = int(date_end.replace(tzinfo=timezone.utc).timestamp())

	#filter training data
	rows = np.where((events_raw[:,3] >= timestamp_start) & (events_raw[:,3] <= timestamp_end))[0]
	events_raw = events_raw[rows]
	labels_raw = labels_raw[rows]

	#print some counts (for humans)
	print("Read", events_raw.shape[0], "events with", events_raw.shape[1], "features")
	print("   ", int(sum(labels_raw)), "events are adoptions")

	#downsample negative events in training data only according to specified ratio
	if downsample_ratio != -1 and scaler == -1:
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
	#if training data but no downsampling, indicate that
	elif scaler == -1:
		print("No downsampling")

	#if testing data, build list of relative dates before killing the time feature
	#1 = first testing day, 30 is last
	relative_days = []
	for event in events_raw:
		'''
		date = datetime.datetime.utcfromtimestamp(event[3])
		print(date)
		print(event[3]-timestamp_start)
		'''
		relative_day = (event[3] - timestamp_start) // 86400 + 1
		relative_days.append(relative_day)

	#convert data to np arrays of correct type, selecting desired features along the way
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
		return events, labels, relative_days
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

results_file = sys.argv[1]		#filename without extension
features = sys.argv[2]			#feature categories to include (character codes)

#set number of iterations for training
num_iter = 50

TEST_DAYS = 7 * 25		#number of days past random day (including random day) to predict
TRAIN_DAYS = 30			#number of days preceding random day to train on

downsample_ratio = 2		#if -1, no downsampling of negative events
				#if a whole number X, sample to have X negative events (non-adopt) for each positive event (adoption)


#set your configuration choices here - dictionary with setting as key, list of choices as value
#loops will test all combinations of these arguments
config_choices = {'loss': ['squared_hinge'], 'penalty': ['l1'], 'shuffle': [True], 'fit_intercept': [False], 'alpha': [0.00001]}

#select the features (columns) to include in training (ranges include first, exclude last, list multiple if desired)
#features = "CUPLS":	U = user, P = pair (user-package), L = library, S = stackoverflow, C = commit
#features selected via command line arg

feature_idx = []	#start with no features, add on what you want
if 'C' in features:
	feature_idx.extend(range(4, 7))		#commit features 4-6
if 'U' in features:
	feature_idx.extend([7, 8, 10, 12, 13, 14, 16, 18])	#user features 7-8, 10, 12-14, 16, 18
if 'P' in features:
	feature_idx.extend(range(23, 29))	#pair (user/library) features 23-28
if 'L' in features:
	feature_idx.extend([29, 30, 32, 35, 37, 38])	#library features 29, 30, 32, 35, 37, 38
if 'S' in features:
	feature_idx.extend(range(40, 44))	#StackOverflow features

feature_idx = np.array(feature_idx)	#convert to numpy array
print("Using features", feature_idx, "\n")

#build list of combinations to pass as arguments to classifier configuration
config_keys = sorted(config_choices)
combos = list(it.product(*(config_choices[key] for key in config_keys)))
print("Testing", len(combos), "classifier configurations\n")
if len(combos) != 1:
	print("pick ONE config!")
	exit(0)

#select a random day between Aug 10, 2016 and Aug 10, 2017
#(need 25 weeks for testing) 
#pick a random number of days between 1 and 365
day_add = random.randint(1, 365)
#add random # of days to first valid date
testing_start = datetime.datetime(2016, 8, 9) + datetime.timedelta(day_add - 1)
testing_end = testing_start + timedelta(days = TEST_DAYS) - timedelta(seconds = 1)
training_end = testing_start - timedelta(seconds = 1)
training_start = testing_start - timedelta(days = TRAIN_DAYS)
print("Training on", training_start.strftime('%b %d %Y'), "through", training_end.strftime('%b %d %Y'), "(" + str(TRAIN_DAYS), "days)")
print("Testing on", testing_start.strftime('%b %d %Y'), "through,", testing_end.strftime('%b %d %Y'), "(" + str(TEST_DAYS), "days)\n")
#print("Training on", training_start, "through", training_end, "(" + str(TRAIN_DAYS), "days)")
#print("Testing on", testing_start, "through,", testing_end, "(" + str(TEST_DAYS), "days)\n")

#load all data covering training + testing range
all_events_raw, all_labels_raw = load_date_range(training_start.year, testing_end.year, training_start.month, testing_end.month)

#load all training data as np array
print("\nTRAINING DATA:")
training_events, training_labels, scaler = load_data(all_events_raw, all_labels_raw, training_start, training_end, downsample_ratio, feature_idx)

#load testing data as np array
print("TESTING DATA:")
testing_events, testing_labels_all, event_relative_days = load_data(all_events_raw, all_labels_raw, testing_start, testing_end, downsample_ratio, feature_idx, scaler)

num_features = testing_events.shape[1]		#grab number of features for csv output

#build list of column headers - will dump data to csv
results = []
results.append(["week", "downsample_ratio", "training days", "training start", "training end", "testing days", "testing start", "testing end", "features", "penalty", "fit_intercept", "loss", "shuffle", "alpha", "num_iter", "true_pos", "true_neg", "false_pos", "false_neg", "precision", "recall", "f1-score", "AUROC"])

#for each configuration combo (just one), run the classifier!
combo = combos[0]
kw = {}
for i in range(0, len(config_keys)):
	kw[config_keys[i]] = combo[i]

#train the classifier
print("Training classifier...")
clf = linear_model.SGDClassifier(n_iter=num_iter, **kw)
print(clf.fit(training_events, training_labels), "\n")
#clf.fit(training_events, training_labels)

print("\ncoefficients:", clf.coef_)
print("intercept:", clf.intercept_, "\n")

#predict all the testing events
predicted_labels_all = clf.predict(testing_events)

#look for adoptions, correctly predicted or not

#how many adoptions in real labels vs predicted?
print(int(sum(testing_labels_all)), "adoption events in", len(testing_labels_all), "import events")
print("predicted", int(sum(predicted_labels_all)), "adoptions")

#divide testing events/labels by week, and build separate lists for each day
testing_labels_by_week = defaultdict(list)
predicted_labels_by_week = defaultdict(list)
for i in range(len(testing_labels_all)):
	day = event_relative_days[i] - 1	#shift range from 1 - TEST_DAYS to 0 - (TEST_DAYS-1)
	week = day // 7
	testing_labels_by_week[week].append(testing_labels_all[i])
	predicted_labels_by_week[week].append(predicted_labels_all[i])
#include an overall accuracy
testing_labels_by_week["all"] = testing_labels_all
predicted_labels_by_week["all"] = predicted_labels_all

#compute stats for each day of testing data
for week in testing_labels_by_week.keys():
	#grab this day's testing and predicted labels
	testing_labels = testing_labels_by_week[week]
	predicted_labels = predicted_labels_by_week[week]

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
	'''
	print("\ntrue pos:", true_pos)
	print("true neg:", true_neg)
	print("false pos:", false_pos)
	print("false neg:", false_neg, "\n")
	print("precision:", precision)
	print("recall:", recall)
	print("F-1 score:", f_score)
	print("AUROC score:", auroc)
	'''

	#append results for this day overall results data
	#["day", "downsample_ratio", "training days", "training start", "training end", "testing days", "testing start", "testing end", "features", "penalty", "fit_intercept", "loss", "shuffle", "alpha", "num_iter", "true_pos", "true_neg", "false_pos", "false_neg", "precision", "recall", "f1-score", "AUROC"]
	results.append([week, downsample_ratio, TRAIN_DAYS, training_start, training_end, TEST_DAYS, testing_start, testing_end, features, kw['penalty'], kw['fit_intercept'], kw['loss'], kw['shuffle'], kw['alpha'], num_iter, true_pos, true_neg, false_pos, false_neg, precision, recall, f_score, auroc])

#save results from all runs to output file, base name specified by command line arg
np.savetxt((results_file + ".csv"), np.array(results), delimiter=",", fmt="%s")
print("\nAll results saved to", results_file + ".csv")


