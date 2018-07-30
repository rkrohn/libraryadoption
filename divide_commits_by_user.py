import json
import os.path
from collections import defaultdict
import pickle

#stream json data one object at a time (generator function)
def stream(f):
	obj_str = ''
	f.read(1) 	#eat first [
	while True:
		c = f.read(1)	#read one character at a time
		#end of file, quit
		if not c:
			#print('EOF')
			break
		#skip newline characters
		if c == '\n':
			continue
		#remove backslashes
		if c == '\'':
			c = '"'
		obj_str = obj_str + c	#add character to current object string
		#when reach end of object, parse json and return resulting object
		if c == '}':
			obj_str = obj_str.replace('u"', '"')	#remove all unicode prefixes
			yield json.loads(obj_str)		#return json object
			obj_str = ''	#clear for next read
			c = f.read(1) 	#eat comma between objects
#end stream

#dump all currently cached data (for a single month) to file
def dump_dict(chunk, name):

	#save dictionary chunk to file
	pik = ("data_files/user_commits/%s_commits.pkl" % name)
	with open(pik, "wb") as f:
		pickle.dump(chunk, f)

	print ("saved %s users for %s user-ids" % (len(chunk), name))
#end dump_dict


#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":
	
	#dictionary of dictionary of commits by user
	#first key: user id / 1000
	#second key: user id
	#value: list of commits by this user, in time-sorted order
	by_user = defaultdict(lambda: defaultdict(list))

	#make sure directory for files exists
	if os.path.isdir("data_files/user_commits") == False:
		os.makedirs("data_files/user_commits")


	#stream data from sorted json files
	for year in range(1993, 1994): #2018):		#read and process 1993 through 2018

		print("Streaming", year)

		#stream from current year's output file
		f = open('data_files/all_commits_by_year/%s_commits_SUB_sorted.json' % year)
		commits = stream(f)

		#process all commits in date order
		for c in commits:
			#grab user from commit
			if c['user'] == '':
				user = 0
			else:
				user = int(c['user'])

			#get user id / 1000 (integer divide)
			mod = user // 1000

			#add this commit to user's list
			by_user[mod][user].append(c)
			
		f.close()

	#save each "chunk" (defined by /1000 key) as a separate pickle
	for key in by_user:
		dump_dict(by_user[key], key)
