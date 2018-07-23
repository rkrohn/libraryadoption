import pickle
import numpy as np

pik = "data_files/new_event_features/2009/1_labels.pkl"

print("LABELS:")
with open(pik, "rb") as f:
	data = pickle.load(f)
	print(len(data), "user-package events")
	print(sum(data), "adoption events")

'''
with open(pik, "rb") as f:
	print(pickle.load(f)[0:10])
'''

pik = "data_files/new_event_features/2009/1_events.pkl"

print("\nDATA:")
with open(pik, "rb") as f:
	data = np.array(pickle.load(f))
	print(len(data), "user-package events with", data.shape[1], "features")

	#count first usages
	#user used package must be false (user not used package before) - idx 22 must be 0
	#user added package must be true (user committed this package) -  idx 20 must be 1
	rows = np.where((data[:,22]==0) & (data[:,20]==1))
	print(len(rows[0]), "first-time usages")

	#repeated usages
	rows = np.where((data[:,22]==1) & (data[:,20]==1))
	print(len(rows[0]), "repeat usages")

	#how many potential adoptions (actually committed or not)
	rows = np.where(data[:,22]==0)
	print(len(rows[0]), "potential adoptions (including actual adoptions and all first-time uses)")

	#count "missed" adoptions - could have been first usage, but wasn't committed
	#user used package must be false (user not used package before) - idx 22 must be 0
	#user added package must be false (user did NOT commit this package) -  idx 20 must be 0
	rows = np.where((data[:,22]==0) & (data[:,20]==0))
	print(len(rows[0]), "missed adoptions")

	#last negative category: used before, but not committed again
	rows = np.where((data[:,22]==1) & (data[:,20]==0))
	print(len(rows[0]), "updated and not committed after previous usage")

	#negative vs positive samples
	print(sum(data[:,20]), "addition events")
	print(len(data) - sum(data[:,20]), "non-additions")


