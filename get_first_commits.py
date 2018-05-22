#extract and parse each user's first commit (any commit) to each repo

import os.path
import subprocess
import sys
import urllib2
import io
import unicodedata
from collections import defaultdict
import file_utils as utils

#--- MAIN EXECUTION BEGINS HERE---#	

#read userid mappings from files
email_to_id = utils.load_json("email_to_userid.json")
name_to_id = utils.load_json("name_to_userid.json")

#get max value (not key) appearing in either dictionary, use as starting point for 
#any new id assignments
max_email = max(email_to_id.values())
max_name = max(name_to_id.values())
if max_name > max_email:
	next_id = max_name + 1
else:
	next_id = max_email + 1

file_idx = 0	#count files as finished

#move to cloned repo directory
os.chdir("repo_clones")	

#for each user, store all of their first commits to any repo
first_commits = defaultdict(list)

#for each cloned repo directory:
for repo in os.listdir("."):
	#not a directory (shouldn't happen), skip
	if os.path.isdir(repo) == False:
		continue
		
	#change into repo dir
	os.chdir(repo)
	
	#run git log, drop in temporary file
	utils.run_bash('''git log --encoding=utf-8 --full-history --reverse "--format=format:%aE, %aN, %at" > ../../temprepolog.txt''' , True)
	
	#change back to parent dir (repo_clones)
	os.chdir("..")
	
	#keep list of users seen in this repo, only save first commit from each
	seen = set()
	
	for line in io.open("../temprepolog.txt", encoding="ISO-8859-1"):
		#extract commit metadata
		commit = [x.strip() for x in line.split(',')]	#email, name, UTC
		#check for diff lines that happen to start with commit flag
		if len(commit) < 3:
			continue
		email = commit[0]	#email is first token
		time = commit[-1]	#time is last token
		#name is all the tokens in the middle
		name = ""
		for token in commit[1:-1]:
			name = name + token
		name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')	

		#mystery committer, just skip and move on
		if name == "" and email == "":
			continue
	
		#find best-guess user matching this name/email pair
		#determine what, if anything, we have seen before
		have_name = name in name_to_id
		have_email = email in email_to_id
		#have neither, assign new id
		if have_name == False and have_email == False:
			if email != "":
				email_to_id[email] = next_id
			if name != "":
				name_to_id[name] = next_id
			user_id = next_id
			next_id = next_id + 1
		#have one or the other (but not both), use id we know for both
		#seen name but not email
		elif have_name == True and have_email == False: 
			if email != "":
				email_to_id[email] = name_to_id[name]
			user_id = name_to_id[name]
		#seen email but not name
		elif have_email == True and have_name == False:
			if name != "":
				name_to_id[name] = email_to_id[email]
			user_id = email_to_id[email]
		#have seen both name and email
		else: #have_email = T and have_name = T
			name_id = name_to_id[name]
			email_id = email_to_id[email]
			#if point to different ids, combine into a single user
			if name_id != email_id:
				email_to_id[email] = name_id
			user_id = name_id
		
		#check if we have seen this user before, if so, skip
		if user_id in seen:
			continue
		
		#store commit info as first commit to this repo by this user, add user to seen
		seen.add(user_id)
		first_commits[name_id].append([repo, time])

	file_idx = file_idx + 1
	if file_idx % 500 == 0:
		print "finished", file_idx, "repos"
		
print "COMPLETE"
os.chdir("..")		

#save results
#save updated user lists
utils.save_json(name_to_id, "name_to_userid.json")
utils.save_json(email_to_id, "email_to_userid.json")
print "final user list saved to name_to_userid.json and email_to_userid.json"

#save first commit info
utils.save_json(first_commits, "first_commits.json")
print "saved first commit data to first_commits.json"