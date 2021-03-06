from bisect import bisect_left

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
time between adoptions within last 10% of adoptions of this package	avg_adopt_delta
time between adoptions within last 10% of all commits			second return of get_deltas
time between commits within last 10% of commits of this package		avg_commit_delta
time between commits within last 10% of all commits			first return of get_deltas
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

	#for this particular package, grab all features and return as vector (list)
	def get_features(self, time, last_commits_start_time):
		vector = []		#build feature vector as list
		
		vector.append(self.add_commits)		#number of commits adding this library
		vector.append(len(self.commit_users))	#number of users who have committed this library
		vector.append(len(self.adopt_users))	#number of users who have adopted = number of adoptions
		vector.append(len(self.repos))		#number of repos containing this library
		vector.append(len(self.adopt_repos))	#number of repos this library was adopted in
		vector.append(time - self.last_adoption if self.last_adoption is not None else None)	#time since last adoption (in seconds)
		vector.append(time - self.last_commit if self.last_commit is not None else None)	#time since last commit (in seconds)
		vector.append(self.avg_adopt_delta)		#avg time between adoptions in last 10% of adoptions
		vector.append(self.avg_commit_delta)		#avg time between commits within last 10% of commits of this package


		commit_delta, adopt_commit_delta = self.get_deltas(last_commits_start_time)	
		vector.append(commit_delta)		#time between commits of this package within last 10% of ALL commits
		vector.append(adopt_commit_delta)	#time between adoptions of this package within last 10% of ALL commits

		return vector
	#end get_features

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

			#update commit history for adoptions of this library
			self.last_adopts, self.avg_adopt_delta = self.update_history(self.last_adopts, self.avg_adopt_delta, len(self.adopt_users), time, adopt)
		
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

	#given a starting timestamp (representing the beginning of the last 10% of ALL commits), compute the average commit delta and average adoption delta after that time for this package
	def get_deltas(self, start_time):
		#do all package commits first
		commit_delta = 0
		pos = bisect_left([i['time'] for i in self.last_commits], start_time)	#index of first eligible commit
		for i in range(pos, len(self.last_commits)-1):
			commit_delta += self.last_commits[i+1]['time'] - self.last_commits[i]['time']
		if len(self.last_commits)-pos-1 > 0:
			commit_delta = commit_delta / (len(self.last_commits)-pos-1)		#divide to get average
		else:
			commit_delta = None

		#then adoption commits
		adopt_delta = 0
		pos = bisect_left([i['time'] for i in self.last_adopts], start_time)	#index of first eligible adoption commit
		for i in range(pos, len(self.last_adopts)-1):
			adopt_delta += self.last_adopts[i+1]['time'] - self.last_adopts[i]['time']
		if len(self.last_adopts)-pos-1 > 0:
			adopt_delta = adopt_delta / (len(self.last_adopts)-pos-1)		#divide to get average
		else:
			adopt_delta = None

		return commit_delta, adopt_delta
	#end get_deltas



