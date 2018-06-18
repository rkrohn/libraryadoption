'''
Package Features - specific to one particular package
*****
# of addition commits					add_commits
# users who have committed				len(commit_users)
# users who have adopted (# adoptions)			len(adopt_users)
# repos containing package				len(repos)
# repos package adopted in				len(adopt_repos)
|{u committed packages} ^ {U_(x in U ^ x adopted i) all committed packages}|
ditto above, for last 10% of commits
Jaccard - {u committed packages} ^ {U committed packages}
    (those last three are specific to the user as well)
time since last adoption				current time - last_adoption
time since last commit					current time - last_commit
time between adoptions within last 10% of adoptions of this package
time between adoptions within last 10% of commits
time between commits within last 10% of commits of this package		avg_commit_delta
time between commits within last 10% of all commits
current rank
    # of adoptions
    # of uses
    # of repos
    # of users using
    # of additions - # deletions (true additions/deletions only)
'''

WINDOW = 0.1		#for windowed stats, take last 10% of a user/repo's commits (once user has at least 5 commits in history)

class Package:
	def __init__(self, name):
		self.name = name		#package/library name
		self.add_commits = 0		#number of addition commits
		self.commit_users = set()	#set of users who have committed this package
		self.adopt_users = set()	#set of users who have adopted this package (equal to total number of adoptions)
		self.repos = set()		#set of repos containing this package
		self.adopt_repos = set()	#set of repos an adoption event of this package occurred in
		self.last_adoption = None	#time of last adoption event for this package
		self.last_commit = None		#time of last add commit for this package

		#windowed history stuff starts here
		self.last_commits = list()	#list of last 10% of commits of this package
		self.avg_commit_delta = None	#average time between commits, taken over last 10% of package commits
		self.last_adopts = list()	#list of last 10% of package's adoption commits
		self.avg_adopt_delta = None	#average time between package adoptions, taken over last 10% of adoption commits

	#given an addition commit by user to repo, log the commit
	def commit_lib(self, user, repo, time, adopt = False):
		self.add_commits += 1
		self.commit_users.add(user)
		self.repos.add(repo)
		self.last_commit = time

		#if commit event was adoption, update that data as well
		if adopt:
			self.adopt_users.add(user)
			self.adopt_repos.add(repo)
			self.last_adoption = time
		
		#update commit history for additions of this library
		self.last_commits, self.avg_commit_delta = self.update_history(self.last_commits, self.avg_commit_delta, self.add_commits, time, adopt)
	#end commit_lib

	#for a given history list, update it to include new commit
	def update_history(self, history_list, history_delta, all_count, time, adopt):
		#update given history list, so that history is limited to 10% of of package's add or adopt commits (once package passes 5 total commits)
		
		#remove earliest commit if history list too long before updating list and delta-t
		num_commits = len(history_list)		#number of commits in current history list

		#if list long enough to remove oldest commit, do that and update
		if (num_commits) / float(all_count) > WINDOW and num_commits > 5:
			removed = history_list.pop(0)	#remove oldest commit
			delta = ((time-history_list[-1]['time']) - (history_list[0]['time']-removed['time'])) / (num_commits-1) #compute change to average intra-commit delta-t
			history_delta = history_delta + delta		#update average intra-commit delta

		#list not too long, just update avg delta-t
		elif num_commits > 1:
			history_delta = ((time-history_list[-1]['time']) + num_commits * history_delta) / num_commits		
		#second commit, explicitly set the average delta
		elif num_commits == 1:
			history_delta = time - history_list[-1]['time']

		#always append newest commit
		history_list.append({'time': time, 'adopt': adopt})

		return history_list, history_delta	#pass by ref doesn't seem to be working, force an overwrite update
	#end update_history


