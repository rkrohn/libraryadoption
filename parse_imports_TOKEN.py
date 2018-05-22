#old, sad code for parsing imports - DON'T USE THIS!

import os.path
import subprocess
import sys
import urllib2
import io
from collections import defaultdict
import unicodedata
import file_utils as utils

#given a line of commit metadata and user dictionaries, returns a user id and timestamp
def get_user_and_time(line, email_to_id, name_to_id):
	line = line.replace("#######", "")
	commit = [x.strip() for x in line.split(',')]	#email, name, UTC
	#check for diff lines that happen to start with commit flag
	if len(commit) < 3:
		return False, False
	email = commit[0]	#email is first token
	time = commit[-1]	#time is last token
	#name is all the tokens in the middle
	name = ""
	for token in commit[1:-1]:
		name = name + token
	name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')
	
	#find user for this commit
	#no name or email, myster committer
	if name == "" and email == "":
		user = -5
	#user name or email to get user id
	elif name != "":
		user = name_to_id[name]
	else:
		user = email_to_id[email]
	
	return user, time

#parses an import line, returns library used
#from x import y OR import x
#want the x's, but also the y's, store as x.y
#for now, leave self-references (.) intact
def parse_import(line):
	#remove leading character (+ or -)
	line = line[1:]
	line = unicodedata.normalize('NFD', line).encode('ascii', 'ignore')
	#check for weird javascript, just throw it out
	if "\\" in line:
		return []
	#tokenize
	line = line.replace(',', ' ')	#replace , with space to tokenize
	tokens = [x.strip() for x in line.split()]
	lib = []

	if len(tokens) == 0:
		return lib
	
	#lots of sad cases
	#	import x				-> x
	# 	import x as y, z as w, ...		-> x, z
	#	from x import y as z, v as w, ...	-> x.y, x.v
	#	from x import y				-> x.y
	#	from x import *				-> x.*

	#if find an as, throw it and the next token out

	#from? from x import y, z -> x.y, x.z
	if tokens[0] == "from" and len(tokens) >= 4:
		base = tokens[1] + "."
		flag = False
		for str in tokens[3:]:
			if flag:
				flag = False
				continue
			if str == "as":		#as? from x import y as z -> x.y
				flag = True
				continue
			lib.append(base + str)
	
	#import? import x, y, z
	elif tokens[0] == "import" and len(tokens) >= 2:
		flag = False
		for str in tokens[1:]:
			if flag:
				flag = False
				continue
			if str == "as":
				flag = True
				continue
			lib.append(str) 

	return lib		

#--- MAIN EXECUTION BEGINS HERE---#	

#read userid mappings from files
email_to_id = utils.load_json("email_to_userid.json")
name_to_id = utils.load_json("name_to_userid.json")

file_idx = 0

#for each commit log file:
for filename in os.listdir('commit_data'):
	commits_list = []	#overall commit list for file
	imports = defaultdict(list)	#import list and count for each commit
	imports_count = 0

	#check if this repo done already
	if os.path.isfile("imports_data/%s.log" % filename[:-12]) == True:
		print filename, "already done"
		continue

	#parse list of commit import statements into more useable form:
	#	list of commits, each with user id, imported libraries, and timestamp

	#loop lines in this file
	for line in io.open("commit_data/%s" % filename, encoding="ISO-8859-1"):
		#commit line
		if line.startswith("#######"):
			#save data from previous commit (if it exists)
			if imports_count != 0:
				commits_list.append([user, time, imports])	#save commit
				imports = defaultdict(list)	#clear list and counts
				imports_count = 0
			#grab new commit data, replace the old
			user, time = get_user_and_time(line, email_to_id, name_to_id)
			if user == False:
				continue			
		#diff line
		else:
			lib = parse_import(line)
			if not lib:	#empty imports, skip
				continue
			imports_count = imports_count + 1
			if line.startswith("+"):
				imports['+'].extend(lib)
			else:
				imports['-'].extend(lib)

	#finished file, save any lingering data
	if imports_count != 0:
		commits_list.append([user, time, imports])	#save commit

	#save file commit data to json
	utils.save_json(commits_list, "imports_data/%s.log" % filename[:-12])

	#period prints
	file_idx = file_idx + 1
	if file_idx % 500 == 0:
		print "finished", file_idx, "files"	

