class Repo:
	def __init__(self, name):
		self.name = name	#repo name
		self.libs = {}		#dictionary of library->last time lib used/updated

	#given library used in the repository, update time of last use
	def use_lib(self, lib, time):
		self.libs[lib] = time

	#return the time of last use for a particular library
	def last_interaction(self, lib):
		return self.libs[lib]
