#first pass at commit parsing - builds (approximate) user list from raw commit data

import os.path
import subprocess
import sys
import urllib2
import io
import unicodedata
import file_utils as utils

#--- MAIN EXECUTION BEGINS HERE---#	

#first step in parsing commit data: creates list of users across all repos, with id, name, and email (not perfect)
email_to_id = utils.load_json("data_files/email_to_userid.json")
name_to_id = utils.load_json("data_files/name_to_userid.json")
if email_to_id == False or name_to_id == False:
	email_to_id = dict()
	name_to_id = dict()

next_id = 0		#keep index of next user id to use
#easy version, find highest id in existing and start one higher than that
for k, v in email_to_id:
	if v > next_id:
		next_id = v + 1
for k, v, in name_to_id:
	if v > next_id:
		next_id = v + 1
file_idx = 0	#count files as finished

mystery_commit_count = 0
mystery_repo_count = 0
mystery_repo_flag = False

#for each commit log file:
for filename in os.listdir('commit_data'):
	#for line in f:
	for line in io.open("commit_data/%s" % filename, encoding="ISO-8859-1"):
		#commit data line
		if line.startswith("#######"):
			#extract commit metadata
			line = line.replace("#######", "")
			commit = [x.strip() for x in line.split(',')]	#email, name, UTC
			#check for diff lines that happen to start with commit flag (sad)
			if len(commit) < 3:
				continue
			email = commit[0]	#email is first token
			time = commit[-1]	#time is last token
			#name is all the tokens in the middle
			name = ""
			for token in commit[1:-1]:
				name = name + token
			#normalize out all the weird characters
			name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')	

			#mystery committer, just skip and move on
			if name == "" and email == "":
				mystery_repo_flag = True
				mystery_commit_count = mystery_commit_count + 1
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
				next_id = next_id + 1
			#have one or the other (but not both), use id we know for both
			#seen email but not name
			elif have_email == True and have_name == False:
				if name != "":
					name_to_id[name] = email_to_id[email]			
			#seen name but not email
			elif have_name == True and have_email == False: 
				if email != "":
					email_to_id[email] = name_to_id[name]
			#have seen both name and email
			else: #have_email = T and have_name = T
				name_id = name_to_id[name]
				email_id = email_to_id[email]
				#if point to different ids, combine into a single user
				if name_id != email_id:
					email_to_id[email] = name_id

	#keep count of repos with mystery commits
	if mystery_repo_flag == True:
		mystery_repo_count = mystery_repo_count + 1
		mystery_repo_flag = False

	#periodic progress prints
	file_idx = file_idx + 1
	if file_idx % 1000 == 0:
		print "finished", file_idx, "files"

print "COMPLETE"		

#count # of users
users = dict((v, k) for k, v in name_to_id.iteritems())
users.update(dict((v, k) for k, v in email_to_id.iteritems()))
print "found", len(users), "users"

#mystery stats - total mystery commits, and number of repos affected
print mystery_commit_count, "mystery commits (not necessarily import commits)"
print mystery_repo_count, "repos affected"

#save results	
utils.save_json(name_to_id, "data_files/name_to_userid.json")
utils.save_json(email_to_id, "data_files/email_to_userid.json")
print "final user list saved to name_to_userid.json and email_to_userid.json"