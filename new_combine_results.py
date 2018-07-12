import glob
import sys
import pandas as pd
import os

def label_training_period(row):
	#single year?
	if row['training_year_first'] == row['training_year_last']:
		#one year?
		if row['training_month_first'] == 1 and row['training_month_last'] == 12:
			return "one year"
		#build label as number of months		
		if row['training_month_first'] == 7 and row['training_month_last'] == 12:
			return "six months"
		if row['training_month_first'] == 12 and row['training_month_last'] == 12:
			return "one month"
	#entire years?
	if row['training_month_first'] == 1 and row['training_month_last'] == 12:
		#two years?
		if row['training_year_last'] - row['training_year_first'] == 1:
			return "two years"
		#build label from year range
		return str(row['training_year_first']) + '-' + str(row['training_year_last'])	
	return "UNDEFINED"
#end label_training_period

def label_testing_period(row):
	#entire years?
	if row['testing_month_first'] == 1 and row['testing_month_last'] == 12:
		return "one year"
	if row['testing_month_first'] == row['testing_month_last']:
		return "one month"
	return "UNDEFINED"
#end label_testing_period

def label_features_removed(row):
	if row['num_features'] == 36:
		return "none"
	if row['num_features'] == 32:
		return "StackOverflow"
	return "UNDEFINED"
#end label_features_removed

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
files = glob.glob('predict_tests/newest_results*')
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

#all compiled, let's improve the format and add a few columns
data = pd.read_csv(filename)

#remove leading/trailing spaces of column headers
data.columns = data.columns.map(lambda x: x.strip())

#same thing for all the data
for column in ['penalty', 'loss', 'fit_intercept', 'shuffle', 'features']:
	data[column] = data[column].map(lambda x: x.strip())

#add some columns for easier sorting/graphing: training period, testing period, features removed
data.insert(5, "training_period", data.apply(label_training_period, axis=1))
data.insert(9, "testing_period", data.apply(label_testing_period, axis=1))
#data.insert(11, "features_removed", data.apply(label_features_removed, axis=1))

#save modified file
data.to_csv(filename, index=False)

print("All data written to", filename)