'''
Package Features - specific to one particular package
*****
# of addition commits
# users who have committed
# users who have adopted (# adoptions)
# repos containing package
# repos package adopted in
|{u committed packages} ^ {U_(x in U ^ x adopted i) all committed packages}|
ditto above, for last 10% of commits
Jaccard - {u committed packages} ^ {U committed packages}
    (those last three are specific to the user as well)
time since last adoption
time since last commit
time between adoptions within last 10% of adoptions of this package
time between adoptions within last 10% of commits
time between commits within last 10% of commits of this package
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

		#update list of last_commits, so that history is limited to 10% of all of package's commits (once package passes 5 total commits)
		
		#remove earliest commit if history list too long before updating list and delta-t
		num_commits = len(self.last_commits)		#number of commits in current history list

		#if list long enough to remove oldest commit, do that and update
		if (num_commits) / float(self.add_commits) > WINDOW and num_commits > 5:
			removed = self.last_commits.pop(0)	#remove oldest commit
			delta = ((time-self.last_commits[-1]['time']) - (self.last_commits[0]['time']-removed['time'])) / (num_commits-1)	#compute change to average intra-commit delta-t
			self.avg_commit_delta += delta		#update average intra-commit delta

		#list not too long, just update avg delta-t
		elif num_commits > 1:
			self.avg_commit_delta = ((time-self.last_commits[-1]['time']) + num_commits * self.avg_commit_delta) / num_commits		
		#second commit, explicitly set the average delta
		elif num_commits == 1:
			self.avg_commit_delta = time - self.last_commits[-1]['time']

		#always append newest commit
		self.last_commits.append({'time': time, 'adopt': adopt})

