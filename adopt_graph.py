from collections import defaultdict
import pickle
import os.path
import glob
import file_utils

#list of adoption events: repo, promoter, adopter, time delay, library, promoter commit id, adopter commit id, promoter commit time, adoption commit time
adopt_events = []	

#history nested dictionary: repo->lib->list of tuples, each is (commit id, user, time)
#use these to get promoters for each adoption event
history = defaultdict(lambda: defaultdict(list))

#time of last interaction of specific user on specific repo: user->repo->time
last_interaction = defaultdict(lambda: defaultdict(int))

unique_libs = set()
unique_users = set()

prev_time = -1

#given a single commit, process and update user/repo library listings and identify any adoption events
def process_commit(c):
	global prev_time, adopt_events

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

	unique_users.add(user)

	#get time of user's last interaction with this repository
	prev_interaction = last_interaction[user][repo]

	#for each library adopted, find and create necessary adoption edges
	for lib in adopted_libs:
		#pull list of promoters/sources
		source_commits = history[repo][lib]

		unique_libs.add(lib)

		#each source generates an adoption "edge" if source commit occurred after user's last interaction with repo
		for source in source_commits:
			#pull source data
			source_id = source[0]		#commit id of source commit
			source_user = source[1]		#promoter
			source_time = source[2]		#time of source commit

			#source commit was before user's last interaction, no adoption edge (assume they saw then and chose not to adopt)
			if source_time < prev_interaction:
				continue

			#build adoption edge list and add to all
			adopt_events.append([repo, source_user, user, time - source_time, lib, source_id, c_id, source_time, time])

	#for each library added, update repo history
	for lib in added_libs:
		history[repo][lib].append((c_id, user, time))

	#update last interaction time between user and repo
	last_interaction[user][repo] = time

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
				print("finished", commit_count, "commits")

	print("Processed", commit_count, "commits, created", len(adopt_events), "adoption edges")

	print("   found", len(unique_libs), "unique libraries adopted")
	print("   found", len(unique_users), "users")

	file_utils.dump_list(adopt_events, ["repo", "promoter", "adopter", "adoption delay (seconds)", "library", "promoter commit id", "adoption commit id", "promoter commit time (UTC)", "adoption commit time (UTC)"], "data_files/adopt_graph_edges_with_times.csv")



