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
import data_utils

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#convert dictionary of unique id->value to value->freq distribution and save as csv file
def save_dist(data, headers, filename):
	dist = data_utils.dict_to_dist(data)
	file_utils.dump_dict_csv(dist, headers, filename)
#end save_dist

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":

	#user data dictionaries
	#key is user, value is count/set
	user_commit_count = defaultdict(int)
	user_adopt_commits = defaultdict(int)
	user_adopt_libs = defaultdict(set)
	user_active_repos = defaultdict(set)
	user_adopt_repos = defaultdict(set)

	#repo data dictionaries
	#key is repo, value is count/set
	repo_commit_count = defaultdict(int)
	repo_adopt_commits = defaultdict(int)
	repo_adopt_libs = defaultdict(set)
	repo_active_users = defaultdict(set)
	repo_adopting_users = defaultdict(set)

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
				adopted_libs = c['adopted_libs']
				adopted = len(adopted_libs)

				#basic commit counts
				user_commit_count[user] += 1
				repo_commit_count[repo] += 1

				#active sets
				user_active_repos[user].add(repo)
				repo_active_users[repo].add(user)

				#adoption counters/sets
				if adopted != 0:
					user_adopt_commits[user] += 1
					repo_adopt_commits[repo] += 1
					user_adopt_repos[user].add(repo)
					repo_adopting_users[repo].add(user)
					for lib in adopted_libs:
						user_adopt_libs[user].add(lib)
						repo_adopt_libs[repo].add(lib)

	#post-process: convert sets to counts of unique items
	for key in user_commit_count.keys():
		user_adopt_libs[key] = len(user_adopt_libs[key])
		user_active_repos[key] = len(user_active_repos[key])
		user_adopt_repos[key] = len(user_adopt_repos[key])
		user_adopt_commits[key] =  user_adopt_commits[key]		#touch in case key not hit

	for key in repo_commit_count.keys():
		repo_adopt_libs[key] = len(repo_adopt_libs[key])
		repo_active_users[key] = len(repo_active_users[key])
		repo_adopting_users[key] = len(repo_adopting_users[key])
		repo_adopt_commits[key] = repo_adopt_commits[key]

	#save raw data to csv
	file_utils.dump_dict_csv([user_commit_count, user_adopt_commits, user_adopt_libs, user_active_repos, user_adopt_repos], ["user", "number of commits", "number of adoption commits", "unique libraries adopted", "unique committing repos", "unique adoption repos"], "results/user_dist/raw_user_data.csv")
	file_utils.dump_dict_csv([repo_commit_count, repo_adopt_commits, repo_adopt_libs, repo_active_users, repo_adopting_users], ["repo", "number of commits", "number of adoption commits", "unique libraries adopted", "unique committing users", "unique adopting users"], "results/repo_dist/raw_repo_data.csv")

	#convert user/repo-specific counts to distributions and save as csv
	save_dist(user_commit_count, ["number of commits", "number of users"], "results/user_dist/commits.csv")
	save_dist(user_adopt_commits, ["number of adoption commits", "number of users"], "results/user_dist/adoption_commits.csv")
	save_dist(user_active_repos, ["number of unique repos interacted with", "number of users"], "results/user_dist/active repos.csv")
	save_dist(user_adopt_repos, ["number of unique repos adopted from", "number of users"], "results/user_dist/adopt_repos.csv")
	save_dist(user_adopt_libs, ["number of unique libraries adopted", "number of users"], "results/user_dist/adopt_libs.csv")

	save_dist(repo_commit_count, ["number of commits", "number of repos"], "results/repo_dist/commits.csv")
	save_dist(repo_adopt_commits, ["number of adoption commits", "number of repos"], "results/repo_dist/adoption_commits.csv")
	save_dist(repo_active_users, ["number of unique committing users", "number of repos"], "results/repo_dist/active_users.csv")
	save_dist(repo_adopting_users, ["number of unique users adopting from", "number of repos"], "results/repo_dist/adopt_users.csv")
	save_dist(repo_adopt_libs, ["number of unique libraries adopted within repo", "number of repos"], "results/repo_dist/adopt_libs.csv")

	print("Results saved to results/user_dist and results/repo_dist")