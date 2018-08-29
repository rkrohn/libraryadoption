import glob
import pickle
from collections import defaultdict
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import file_utils

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#--- MAIN EXECUTION BEGINS HERE---#

#flags and values to set operating mode
BIN_WIDTH = 5				#sets number of minutes per bin
PRE_WIN = 6 * 3600			#amount of time, in seconds, to include in the pre-commit activity window
POST_WIN = 6 * 3600			#time, in seconds, to include in post-commit activity window
MAX_USER_COMMITS = 10000	#maximum number of user commits for consideration

#get list of user commit files to process
files = glob.glob('data_files/user_commits/*')
print("Processing", len(files), "user commit files")

#global counters
total_user_count = 0	#used for final print statement only - number of users actually considered for activity analysis
total_all_user_count = 0	#number of users available
total_commit_count = 0		#total number of commits processed (for print only)
total_adopt_commits = 0			#number of adoption commits stacked
total_reg_commits = 0			#number of non-adopt commits stacked for comparison against adopt commits
total_import_commits = 0		#number of non-adopt import commits stacked for comparison against adopt commits

#commit activity variables
adopt_activity_counts = defaultdict(int)	#key is minutes from adoption commit (pos or neg, in BIN_WIDTH increments)
											#value is # of commits made at that time (across all adopt commits by all users)
reg_activity_counts = defaultdict(int)		#same as above, but for all regular non-adopt commits
import_activity_counts = defaultdict(int)	#same as above, but for non-adopt import commits

#process each file one at a time
for file in files:
	print("\nProcessing", file)

	user_commits = load_pickle(file)
	total_all_user_count += len(user_commits)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		#if user has too many commits, skip
		if len(commits) > MAX_USER_COMMITS:
			continue

		total_user_count += 1	#count users considered, not all of them

		#user variables
		user_adopt_commits = 0	#number of adoption commits by user

		#commit indices
		pre_start = 0			#index of first commit included in pre-commit activity window
		post_end = 0			#index of first commit excluded from post-commit activity window

		total_commit_count += len(commits)		#add users's commits to total count

		#loop all commits made by this user
		for i in range(0, len(commits)):

			#grab current commit for easier access
			c = commits[i]	

			#move up pre_start index if necessary so that commit it points to falls within PRE_WIN
			#do this for all commits, just to keep indices up to date
			while c['time'] - commits[pre_start]['time'] > PRE_WIN:
				pre_start += 1
			#move up post_end index if necessary so that commit it points to falls outside POST_WIN
			while post_end < len(commits) and commits[post_end]['time'] - c['time'] < POST_WIN:
				post_end += 1

			#extract commits that fall within defined activity window (may not use them)
			surrounding_commits = commits[pre_start:post_end]	

			#if current commit contains an adoption, if so add to adoption stack
			if c['adopted_libs']: 
				user_adopt_commits += 1	
				total_adopt_commits += 1	
				#for each commit within activity window, compute "minutes from commit" and add to relevant bin counter
				for a in surrounding_commits:
					adopt_activity_counts[int((a['time'] - c['time']) / (BIN_WIDTH * 60))*BIN_WIDTH] += 1

			#if commit contains no adoptions, add to regular commit stack
			else:
				total_reg_commits += 1
				#for each commit within activity window, compute "minutes from commit" and add to relevant bin counter
				for a in surrounding_commits:
					reg_activity_counts[int((a['time'] - c['time']) / (BIN_WIDTH * 60))*BIN_WIDTH] += 1

			#if import commit but no adoption (ie, added libraries but none were adoptions), add to import commit stack
			if len(c['adopted_libs']) == 0 and c['add_libs']:
				total_import_commits += 1
				#for each commit within activity window, compute "minutes from commit" and add to relevant bin counter
				for a in surrounding_commits:
					import_activity_counts[int((a['time'] - c['time']) / (BIN_WIDTH * 60))*BIN_WIDTH] += 1

		#wrap up current user before moving to next
		print("User", user, "made", len(commits), "commits (" + str(user_adopt_commits), "adoption commits)")		

print("Processed", total_commit_count, "commits and", total_user_count, "users")
print("   ", total_adopt_commits, "adoption commits")
print("   ", total_reg_commits, "non-adopt commits (import and not)")
print("   ", total_import_commits, "non-adopt import commits (added libraries)")

#post-process totals for plotting
#get list of keys (times) that occur in any activity dictionary
times = sorted(list(adopt_activity_counts.keys()) + list(set(reg_activity_counts.keys()) - set(adopt_activity_counts.keys())))
times = sorted(list(times) + list(set(import_activity_counts.keys()) - set(times)))

#divide commits activity totals by total number of commits (compute average)
for key in times:
	adopt_activity_counts[key] /= total_adopt_commits
	reg_activity_counts[key] /= total_reg_commits
	import_activity_counts[key] /= total_import_commits

#save all data to csv
file_utils.dump_dict_csv([adopt_activity_counts, reg_activity_counts, import_activity_counts], ["time from commit (minutes)", "adoption commits", "non-adopt commits (all)", "non-adopt import commits (added lib)"], "results/activity_analysis/commit_activity_data_%smin_%sK_max_commits.csv" % (BIN_WIDTH, int(MAX_USER_COMMITS / 1000)))

#plot all three lines on the same plot (since this is just for verification)
plt.clf()
fig, ax = plt.subplots()
#adoption
x, y = zip(*sorted(adopt_activity_counts.items()))
ax.plot(x, y, 'r', label='adoption commits')
#all non-adopt
x, y = zip(*sorted(reg_activity_counts.items()))
ax.plot(x, y, 'b', label='all non-adopt commits')
#import non-adopt
x, y = zip(*sorted(import_activity_counts.items()))
ax.plot(x, y, 'g', label='non-adopt import commits')
plt.legend(loc='best')
plt.axvline(x=0, color='k', lw=0.4)
plt.yscale('log')
plt.savefig("results/activity_analysis/commit_activity_%smin_%sK_max_commits.png" % (BIN_WIDTH, int(MAX_USER_COMMITS / 1000)), bbox_inches='tight')

print("Comarison plots and raw data saved to results/activity_analysis/commit_activity_%smin_%sK_max_commits.png and results/activity_analysis/commit_activity_%smin_%sK_max_commits.csv" % (BIN_WIDTH, int(MAX_USER_COMMITS / 1000), BIN_WIDTH, int(MAX_USER_COMMITS / 1000)))

