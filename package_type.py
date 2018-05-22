#this file contains the sub-module flag for all python scripts that use items
#provides one method that returns the corresponding type subscript based on flag value
#also prints the current flag state

def get_type():

	#flag to determine how to count/parse libraries and adoptions
	#if true, take import exactly as given, submodules/packages included (ie, os.path)
	#if false, only take top package level, strip submodules (ie, os only)
	
	SUB_PACKAGE = False	

	#file count-type specifier
	if SUB_PACKAGE:
		print "Preserving submodules"
		type_subscript = "SUB"
	else:
		print "Using top-level packages only"
		type_subscript = "TOP"
		
	return type_subscript
	
	
	
import package_type
package_type.get_type()