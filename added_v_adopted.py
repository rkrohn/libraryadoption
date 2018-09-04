from collections import defaultdict
import pickle
import os.path
import glob
import file_utils
import random

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":

	commit_count = 0
	commit_tuples = []			#list of lists, one per commit - each list contains # of libraries added, # of libraries deleted, and # of libraries adopted in that commit
	commit_tuples_filtered = []		#same as above, but filtered to only the commits with an adoption

	#get list of month commit files to process
	files = glob.glob('data_files/augmented_commits/*')
	print("Processing", len(files), "monthly commit files")

	#process each file one at a time
	for file in sorted(files):
		print("Processing", file)

		commits = load_pickle(file)

		#process all commits in date order
		for c in commits:

			commit_row = []
			commit_row.append(len(c['add_libs']))
			commit_row.append(len(c['del_libs']))
			commit_row.append(len(c['adopted_libs']))
			commit_tuples.append(commit_row)

			if c['adopted_libs']:
				commit_tuples_filtered.append(commit_row)

			#update commit counter
			commit_count += 1
			if commit_count % 1000 == 0:
				print("finished", commit_count, "commits")

	print("Processed", commit_count, "commits, found", len(commit_tuples_filtered), "commits with adoption")

	#sample down
	commit_tuples_sampled = random.sample(commit_tuples, 50000)
	commit_tuples_filtered_sampled = random.sample(commit_tuples_filtered, 50000)

	#full output
	file_utils.dump_list(commit_tuples, ["libs added", "libs deleted", "libs adopted"], "results/commit_scatter.csv")
	file_utils.dump_list(commit_tuples_filtered, ["libs added", "libs deleted", "libs adopted"], "results/commit_scatter_adopt_only.csv")
	print("Full output saved to results/commit_scatter.csv and results/commit_scatter_adopt_only.csv")

	#sampled output
	file_utils.dump_list(commit_tuples_sampled, ["libs added", "libs deleted", "libs adopted"], "results/commit_scatter_50K.csv")
	file_utils.dump_list(commit_tuples_filtered_sampled, ["libs added", "libs deleted", "libs adopted"], "results/commit_scatter_adopt_only_50K.csv")
	print("Sampled output saved to results/commit_scatter_50K.csv and results/commit_scatter_adopt_only_50K.csv")


