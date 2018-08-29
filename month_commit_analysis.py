import os.path
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta
import glob
import sys
import pandas as pd
import os
import pickle
from math import ceil
import file_utils
import plot_utils

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":

	#store month counts as dictionaries - key is month-year, value is count	
	overall_count = 0
	month_count = defaultdict(int)

	import_commit_count = 0
	month_import_commit_count = defaultdict(int)

	addition_commit_count = 0
	month_addition_commit_count = defaultdict(int)

	deletion_commit_count = 0
	month_deletion_commit_count = defaultdict(int)

	additions_count = 0
	month_additions_count = defaultdict(int)

	deletions_count = 0
	month_deletions_count = defaultdict(int)

	additions = set([])
	month_additions = defaultdict(set)

	deletions = set([])
	month_deletions = defaultdict(set)

	adoption_commit_count = 0
	month_adoption_commit_count = defaultdict(int)

	adoption_libs_count = 0
	month_adoption_libs_count = defaultdict(int)

	adoptions = set([])
	month_adoptions = defaultdict(set)

	all_libs = set([])
	month_libs = defaultdict(set)

	all_users = set([])
	month_users = defaultdict(set)

	all_repos = set([])
	month_repos = defaultdict(set)

	user_adopt = set([])
	month_user_adopt = defaultdict(set)

	repo_adopt = set([])
	month_repo_adopt = defaultdict(set)

	#get list of user commit files to process
	files = glob.glob('data_files/user_commits/*')
	print("Processing", len(files), "user commit files")

	#process each file one at a time
	for file in files:
		print("Processing", file)

		user_commits = load_pickle(file)

		#for each user in this chunk, step through their commits
		for user, commits in user_commits.items():

			#process all commits in date order
			for c in commits:
				#grab commit fields: user, repo, time, added_libs, and deleted_libs
				repo = c['repo']
				time = int(c['time'])
				added_libs = c['add_libs']
				deleted_libs = c['del_libs']
				adopted_libs = c['adopted_libs']
				if c['user'] == '':
					user = 0
				else:
					user = int(c['user'])

				#get month-year key from this commit time
				date = datetime.fromtimestamp(time)
				key = date.strftime('%Y-%m')

				#overall counts
				overall_count += 1
				month_count[key] += 1

				#added/deleted libs counts
				added = len(added_libs)
				deleted = len(deleted_libs)

				if added != 0 or deleted != 0:
					import_commit_count += 1
					month_import_commit_count[key] += 1

				if added != 0:
					addition_commit_count += 1
					month_addition_commit_count[key] += 1
					additions_count += added
					month_additions_count[key] += added
					for lib in added_libs:
						additions.add(lib)
						month_additions[key].add(lib)
						all_libs.add(lib)
						month_libs[key].add(lib)

				if deleted != 0:
					deletion_commit_count += 1
					month_deletion_commit_count[key] += 1
					deletions_count += deleted
					month_deletions_count[key] += deleted
					for lib in deleted_libs:
						deletions.add(lib)
						month_deletions[key].add(lib)
						all_libs.add(lib)
						month_libs[key].add(lib)

				#adoption counts
				adopted = len(adopted_libs)
				if adopted != 0:
					adoption_commit_count += 1
					month_adoption_commit_count[key] += 1
					adoption_libs_count += adopted
					month_adoption_libs_count[key] += adopted
					for lib in adopted_libs:
						adoptions.add(lib)
						month_adoptions[key].add(lib)
						all_libs.add(lib)
						month_libs[key].add(lib)

				#user sets
				all_users.add(user)
				month_users[key].add(user)
				if adopted != 0:
					user_adopt.add(user)
					month_user_adopt[key].add(user)

				#repo sets
				all_repos.add(repo)
				month_repos[key].add(repo)
				if adopted != 0:
					repo_adopt.add(repo)
					month_repo_adopt[key].add(repo)

	#post-process: convert sets to counts of unique items
	for key in month_users.keys():
		month_additions[key] = len(month_additions[key])
		month_deletions[key] = len(month_deletions[key])
		month_adoptions[key] = len(month_adoptions[key])
		month_users[key] = len(month_users[key])
		month_repos[key] = len(month_repos[key])
		month_user_adopt[key] = len(month_user_adopt[key])
		month_repo_adopt[key] = len(month_repo_adopt[key])
		month_libs[key] = len(month_libs[key])

	#add total dictionaries so appears in final csv
	month_count['total'] = overall_count
	month_import_commit_count['total'] = import_commit_count
	month_addition_commit_count['total'] = addition_commit_count
	month_deletion_commit_count['total'] = deletion_commit_count
	month_additions_count['total'] = additions_count
	month_deletions_count['total'] = deletions_count
	month_additions['total'] = len(additions)
	month_deletions['total'] = len(deletions)
	month_adoption_commit_count['total'] = adoption_commit_count
	month_adoption_libs_count['total'] = adoption_libs_count
	month_adoptions['total'] = len(adoptions)
	month_users['total'] = len(all_users)
	month_repos['total'] = len(all_repos)
	month_user_adopt['total'] = len(user_adopt)
	month_repo_adopt['total'] = len(repo_adopt)
	month_libs['total'] = len(all_libs)

	#save data to csv
	file_utils.dump_dict_csv([month_count, month_import_commit_count, month_libs, month_addition_commit_count, month_additions_count, month_additions, month_deletion_commit_count, month_deletions_count, month_deletions, month_adoption_commit_count, month_adoption_libs_count, month_adoptions, month_users, month_repos, month_user_adopt, month_repo_adopt], ["year-month", "number of commits", "number of import commits", "unique libraries committed (add-del-or-adopt)", "number of addition commits", "number of libraries added", "unique libraries added", "number of deletion commits", "number of libraries deleted", "unique libraries deleted", "number of adoption commits", "number of libraries adopted", "unique libraries adopted", "unique active users", "unique active repos", "unique adopting users", "unique repos with adoption"], "results/commit_analysis_by_month.csv")