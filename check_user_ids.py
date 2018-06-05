#given finished name/email to user id mapping files, 

import file_utils as utils
import data_utils as data

#--- MAIN EXECUTION BEGINS HERE---#	

#loop name/email mappings
email_to_id = utils.load_json("data_files/email_to_userid.json")
name_to_id = utils.load_json("data_files/name_to_userid.json")

#count # of users
name_users = data.flip_dict(name_to_id)
email_users = data.flip_dict(email_to_id)
print "found", len(name_users), "name users"
print "found", len(email_users), "email users"

#count total number of users
users = dict((v, k) for k, v in name_to_id.iteritems())
users.update(dict((v, k) for k, v in email_to_id.iteritems()))
print "found", len(users), "total users"

#users with more than one email?
max_email = 0
multi_email = 0
for k, v in email_users.iteritems():
	if len(v) > max_email:
		max_email = len(v)
	if len(v) > 1:
		multi_email += 1
print "max email addresses per user:", max_email
print "number of users with multiple email addresses:", multi_email		
		
max_name = 0
multi_name = 0
for k, v in name_users.iteritems():
	if len(v) > max_name:
		max_name = len(v)
	if len(v) > 1:
		multi_name += 1
print "max names per user:", max_name
print "number of users with multiple names", multi_name		
		