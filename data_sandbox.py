import pickle
import numpy as np
from datetime import datetime
import os

pik = "data_files/new_event_features/2007/3_updated_labels.pkl"

with open(pik, "rb") as f:
	data = pickle.load(f)
	print(len(data), "labels")
	print(sum(data), "adoptions")

pik = "data_files/new_event_features/2007/3_labels.pkl"

with open(pik, "rb") as f:
	data = pickle.load(f)
	print(len(data), "labels")
	print(sum(data), "adoptions")

exit(0)

pik = "data_files/user_commits/119_commits.pkl"

with open(pik, "rb") as f:
	data = pickle.load(f)
	print(len(data), "users")

	print(len(data[119161]))
	print(len(data[119162]))
	print(len(data[119163]))
	print(len(data[119164]))
	#119163

exit(0)

for filename in sorted(os.listdir("data_files/augmented_commits")):
	print(filename)

	#get date of this filename
	year = filename[:4]
	month = filename[5:7]

	#build new (correct) filename
	#decrement month
	month_int = int(month) - 1
	year_int = int(year)
	#if month 0, roll back year as well
	if month_int == 0:
		month_int = 12
		year_int -= 1
	#new filename
	new_filename = "data_files/augmented_commits/%s_commits.pkl" % ("%s-%s" % (year_int, str(month_int) if len(str(month_int)) == 2 else "0" + str(month_int)))
	print(new_filename)

	#rename file
	os.rename("data_files/augmented_commits/" + filename, new_filename)


exit(0)


pik = "data_files/augmented_commits/1990-09_commits.pkl"

with open(pik, "rb") as f:
	data = pickle.load(f)
	print(len(data))

	for c in data:
		print(datetime.fromtimestamp(c['time']).month)


exit(0)

pik = "data_files/user_commits/16_commits.pkl"

with open(pik, "rb") as f:
	data = pickle.load(f)
	print(list(data.keys()))
	for key in data:
		prev = -1
		flag = False
		for c in data[key]:
			if c['time'] < prev:
				flag = True
				print("crap")
			prev = c['time'] 
		if flag == False:
			print("all good")

exit(0)

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

	#negative vs positive samples
	print(sum(data[:,20]), "addition events")
	print(len(data) - sum(data[:,20]), "skipped adoptions (anti-add)")


