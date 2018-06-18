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
