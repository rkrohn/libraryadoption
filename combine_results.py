import glob
import sys

#--- MAIN EXECUTION BEGINS HERE---#

#verify filename for output file
if len(sys.argv) < 2:
	print("Requires command line argument for results filename. Exiting")
	exit(0)
filename = sys.argv[1]

#get list of files to combine
files = glob.glob('predict_tests/results*')
print("Combining", len(files), "files")

fout = open(filename, "a")	#open output file

#copy entire contents of first file
for line in open(files[0]):
	fout.write(line)

#copy just the data of all remaining files, skipping the headers   
for idx in range(1, len(files)):
	f = open(files[idx])
	f.__next__() 		#skip header line
	for line in f:
		fout.write(line)	#write all data lines
	f.close()

#close output file
fout.close()
print("All data written to", filename)

