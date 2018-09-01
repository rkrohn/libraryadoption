import glob
import sys
import pandas as pd
import os

#--- MAIN EXECUTION BEGINS HERE---#

#verify filename for output file
if len(sys.argv) < 2:
	print("Requires command line argument for results filename. Exiting")
	exit(0)
filename = sys.argv[1]

#delete file if already exists (replace it)
if os.path.exists(filename):
	os.remove(filename)

#get list of files to combine
files = glob.glob('predict_tests/results_by_day_*combined.csv')
print("Combining", len(files), "files")

fout = open(filename, "a")	#open output file

#copy header row of first file
for line in open(files[0]):
	fout.write(line)
	break

#copy data rows of all remaining files, but only if row contains "all" (indicating is 30 prediction score, not individual day)
for idx in range(0, len(files)):
	f = open(files[idx])
	f.__next__() 		#skip header line
	for line in f:
		if "all" in line:
			fout.write(line)	#write all data lines
	f.close()

#close output file
fout.close()

#skip all this - post-process later
'''
#all compiled, let's improve the format and add a few columns
data = pd.read_csv(filename)

#remove leading/trailing spaces of column headers
data.columns = data.columns.map(lambda x: x.strip())

#same thing for all the data
for column in ['penalty', 'loss', 'fit_intercept', 'shuffle', 'features']:
	data[column] = data[column].map(lambda x: x.strip())

#add some columns for easier sorting/graphing: training period, testing period, features removed
data.insert(7, "training_period", data.apply(label_training_period, axis=1))
data.insert(11, "testing_period", data.apply(label_testing_period, axis=1))

#save modified file
data.to_csv(filename, index=False)
'''

print("All data written to", filename)