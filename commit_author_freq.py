#count frequency of each commit author name and email, so we can track down the ones breaking id assignment

import os.path
import subprocess
import sys
import urllib2
import io
import unicodedata
from collections import defaultdict
import file_utils as utils
import data_utils as data
import operator

#--- MAIN EXECUTION BEGINS HERE---#	

name_count = utils.load_json("data_files/author_name_freq.json")
email_count = utils.load_json("data_files/author_email_freq.json")

#build list if does not exist
if name_count == False or email_count == False:

	#dictionary for name and email counts
	name_count = defaultdict(int)
	email_count = defaultdict(int)

	file_idx = 0

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

				name_count[name] += 1
				email_count[email] += 1
			
		#periodic progress prints
		file_idx = file_idx + 1
		if file_idx % 1000 == 0:
			print "finished", file_idx, "files"

	print "COMPLETE"

#have lists, convert back to dictionary for sorting
else:
	name_count = dict(name_count)
	email_count = dict(email_count)	

#remove all names/emails that only occur once
name_count = dict((k, v) for k, v in name_count.iteritems() if v > 1)
email_count = dict((k, v) for k, v in email_count.iteritems() if v > 1)

#sort
name_count = sorted(name_count.items(), key=operator.itemgetter(1), reverse=True)
email_count = sorted(email_count.items(), key=operator.itemgetter(1), reverse=True)	

#save results	
utils.save_json(name_count, "data_files/author_name_freq.json")
utils.save_json(email_count, "data_files/author_email_freq.json")
