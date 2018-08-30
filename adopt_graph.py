from collections import defaultdict
import pickle
import os.path
import glob
import file_utils

HISTORY_LIMIT = 30 		#number of days of history to consider for adoption sources

#list of adoption events: library, promote commit id, promoter, promote repo, promote commit time, adopt commit id, adopter, adopt repo, adopt commit time, time delay
adopt_events = []	

#history nested dictionary: lib->repo->list of tuples, each is (commit id, user, repo, time)
#use these to get promoters for each adoption event
history = defaultdict(lambda: defaultdict(list))

#set of repos each user is active in: user->set of repos
active_repos = defaultdict(set)

unique_adopted_libs = set()
unique_users = set()
adopt_users = set()
graph_users = set()

prev_time = -1

#given a single commit, process and update user/repo library listings and identify any adoption events
def process_commit(c):
	global prev_time

	#grab commit fields: id, user, repo, time, added_libs, and adopted_libs
	c_id = c['id']
	repo = c['repo']
	time = int(c['time'])
	adopted_libs = c['adopted_libs']
	added_libs = c['add_libs']
	if c['user'] == '':
		print(c)
		user = 0
	else:
		user = int(c['user'])

	#sanity check: if ever the commits are not in time order, throw error and quit
	if prev_time == -1:
		prev_time = time
	if time < prev_time:
		print("ORDER FAIL")
		exit(0)

	#add repo to user's active list
	active_repos[user].add(repo)

	#keep track of unique users (any commit) and unique adoption users (adoption commits only)
	unique_users.add(user)
	if len(adopted_libs) != 0:
		adopt_users.add(user)

	#grab set of repos committed to by this user 
	user_repos = active_repos[user]

	#for each library adopted, find and create necessary adoption edges
	for lib in adopted_libs:

		unique_adopted_libs.add(lib)	#add lib to set of adopted
		graph_users.add(user)			#add user to set of graph nodes

		#pull history for this library (across all repos)
		lib_history = history[lib]

		#loop repos user is active in
		for watched_repo in user_repos:

			#update this repo's history to only contain commits from the last HISTORY_LIMIT days
			lib_history[watched_repo][:] = [tup for tup in lib_history[watched_repo] if time - tup[3] <= HISTORY_LIMIT * 86400]

			#for each repo, loop potential library sources/promoters: each of these sources generates an adoption edge
			for source in lib_history[watched_repo]:

				#pull source data
				source_id = source[0]		#commit id of source commit
				source_user = source[1]		#promoter
				source_repo = source[2]		#repo of promotion commit
				source_time = source[3]		#time of source commit

				#build adoption edge list and add to all
				#library, promote commit id, promoter, promote repo, promote commit time, adopt commit id, adopter, adopt repo, adopt commit time, time delay
				adopt_events.append([lib, source_id, source_user, source_repo, source_time, c_id, user, repo, time, time - source_time])
				graph_users.add(source_user)	#add source user to node set

	#for each library added, update repo history
	for lib in added_libs:
		history[lib][repo].append((c_id, user, repo, time))

	return
#end process_commit

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":
	global adopt_events

	commit_count = 0

	#get list of month commit files to process
	files = glob.glob('data_files/augmented_commits/*')
	print("Processing", len(files), "monthly commit files")

	#process each file one at a time
	for file in sorted(files):
		print("Processing", file)

		commits = load_pickle(file)

		#process all commits in date order
		for c in commits:

			process_commit(c)		#process this commit

			#update commit counter
			commit_count += 1
			if commit_count % 1000 == 0:
				print("finished", commit_count, "commits, found", len(adopt_events), "adoption edges")

	print("Processed", commit_count, "commits, created", len(adopt_events), "adoption edges")

	print("   found", len(unique_adopted_libs), "unique libraries adopted")
	print("   found", len(unique_users), "unique users in all commits")
	print("   found", len(adopt_users), "unique users adopting")
	print("   found", len(graph_users), "users in adoption graph")

	#library, promote commit id, promoter, promote repo, promote commit time, adopt commit id, adopter, adopt repo, adopt commit time, time delay
	file_utils.dump_list(adopt_events, ["library", "promoter commit id", "promoter", "promote repo", "promote commit time (UTC)", "adopt commit id", "adopter", "adopt repo", "adopt commit time (UTC)", "time delay (seconds)"], "data_files/adopt_graph_edges.csv")
	print("Output saved to data_files/adopt_graph_edges.csv")


