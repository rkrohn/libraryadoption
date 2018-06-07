#first pass at commit parsing - builds (approximate) user list from raw commit data
#creates list of users across all repos, with id, name, and email (not perfect)

import os.path
import subprocess
import sys
import urllib2
import io
import unicodedata
import file_utils as utils
import data_utils as data

#given a dictionary of the form key->set of values, add a new value to a particular key's list
def add_to_dict_set(dict, key, new_val):
	if key not in dict:
		dict[key] = set()
	dict[key].add(new_val)
#end add_to_dict_set

#given a dictionary, return the largest value (not key) in the dictionary
def largest_dict_val(dict):
	key_max = max(dict.keys(), key=(lambda k: dict[k]))
	return dict[key_max]
#end largest_dict_val

#--- MAIN EXECUTION BEGINS HERE---#	

#check if this step already completed
email_to_id = utils.load_json("data_files/email_to_userid.json")
name_to_id = utils.load_json("data_files/name_to_userid.json")
if email_to_id != False or name_to_id != False:
	print "list already exists, exiting"
	exit(0)
#no lists, create new dictionaries
else:
	email_to_id = dict()
	name_to_id = dict()

#correlate both ways - sad, but makes the combining correct
id_to_email = dict()
id_to_name = dict()

#bring id to other up to date based on read-in mapping
#legacy - only impacts if are starting from an existing list
if len(email_to_id) != 0:
	id_to_name = data.flip_dict_set(name_to_id)
	id_to_email = data.flip_dict_set(email_to_id)

next_id = 0		#keep index of next user id to use

#legacy again - if building off existing user list, id counter can't start at 0
#easy version, find highest id in existing and start one higher than that
if len(email_to_id) != 0:
	next_id = max(next_id, largest_dict_val(email_to_id)+1, largest_dict_val(name_to_id)+1)

print next_id

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

			#special-case some troublesome names and emails - set to "" instead
			if name == "Unknown" or name == "root" or name == "(no author)" or name == "unknown":
				name = ""	
			if email == "none@none" or email == "" or email == "unknown" or email == "Unknown":
				email == ""

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
					add_to_dict_set(id_to_email, email, next_id)
				if name != "":
					name_to_id[name] = next_id
					add_to_dict_set(id_to_name, name, next_id)
				next_id = next_id + 1
			#have one or the other (but not both), use id we know for both
			#seen email but not name
			elif have_email == True and have_name == False and name != "":
				email_id = email_to_id[email]
				name_to_id[name] = email_id
				add_to_dict_set(id_to_name, name, email_id)			
			#seen name but not email
			elif have_name == True and have_email == False and email != "": 
				name_id = name_to_id[name]
				email_to_id[email] = name_id
				add_to_dict_set(id_to_email, email, name_id)
			#have seen both name and email, combine into single user
			elif have_email == True and have_name == True:
				name_id = name_to_id[name]
				email_id = email_to_id[email]
				#if point to different ids, combine into a single user
				if name_id != email_id:
					#get list of names using 'old' id, and remove from that dictionary
					update_names = id_to_name.pop(name_id, None)
					#assign email_id (arbitrary choice) to all of user's names
					if update_names is not None:
						id_to_name[email_id].update(update_names)
						for n in update_names:
							name_to_id[n] = email_id
					#get list of emails using 'old' id, and remove from that dictionary
					update_emails = id_to_email.pop(name_id, None)
					#assign email_id (arbitrary choice) to all of user's emails
					if update_emails is not None:
						id_to_email[email_id].update(update_emails)
						for e in update_emails:
							email_to_id[e] = email_id

					
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