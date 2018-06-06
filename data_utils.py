from collections import defaultdict

#given a user, repo, time triple, create a dictionary containing those values
def build_dict(user, repo, time):
	d = {}
	d["user"] = user
	d["repo"] = repo
	d["time"] = time
	return d
	
#given a dict with user, repo, time keys, unfold it
def unfold_dict(d):
	return d["user"], d["repo"], d["time"]
	
#given a dictionary of key->value, return a new dict of value->list of keys
#if given a second parallel dict using same keys, values in new dict will be tuples
def flip_dict(dict, parallel = None):
	flip = defaultdict(list)
	for k, v in dict.iteritems():
		if parallel == None:
			flip[v].append(k)
		else:
			flip[v].append((k, parallel[k]))
	return flip

#given a dictionary of key->value, return a new dict of value->set of keys
#if given a second parallel dict using same keys, values in new dict will be tuples
def flip_dict_set(dict, parallel = None):
	flip = defaultdict(set)
	for k, v in dict.iteritems():
		if parallel == None:
			flip[v].add(k)
		else:
			flip[v].add((k, parallel[k]))
	return flip

	
#given a sequence of values and a single value x, compute the CDF of x in that sequence
#if list is sorted and supply an index, should run faster
#returns value between 0 and 1	
def get_cdf(seq, x, index = -1):
	count = 0
	if index == -1:
		for value in seq:
			if value <= x:
				count = count + 1
	else:
		count = index
	prob = float(count) / float(len(seq))
	return prob	