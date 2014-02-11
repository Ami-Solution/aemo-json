import os
import datetime
import csv
import urllib, urllib2
from zipfile import ZipFile
import json

# parameters
url_base = 'http://www.nemweb.com.au'
url_dir = url_base + '/mms.GRAPHS/GRAPHS/'
states = ["VIC","NSW","SA","QLD","TAS"]

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Structure to store the data from the CSV
info_dict = {}

for state in states:

	# Opening u the relevant file for this state
	fn, d = urllib.urlretrieve(url_dir+"GRAPH_30"+state+"1.csv")
	#print 'Local copy (spreadsheet) is at: '+fn2
	f = open(fn,'U')

	# It's a CSV file - we extract info in a format ready to be JSONified
	reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)

	for row in reader:
		# First 1 row contains headers
		if reader.line_num < 2:
			continue
		# Subsequent rows contain the information we populate the dictionary with
		# VIC1,"2014/02/02 09:00:00",5449.02,45.99,TRADE
		if len(row)>4:
			f_date = row[1].split(" ")[0].replace("\"", "")
			f_time = row[1].split(" ")[1].replace("\"", "")
			f_demand = row[2]
			f_price = row[3]
			# Type: as traded, or projected
			f_type = row[4]

			# Building a nested dictionary: state => day => time => quantities
			if info_dict.has_key(state):
				pass
			else:
				info_dict[state]={}

			if info_dict[state].has_key(f_date):
				pass
			else:
				info_dict[state][f_date]={}

			info_dict[state][f_date][f_time]={
				"demand": f_demand,
				"price": f_price,
				"type": f_type
			}

	f.close()

# Outputting the dictionary for RTEM application
jf = open('../data/dmd-price-30mn.json','w')
jf.write(json.dumps(info_dict,sort_keys=True, indent=4))
jf.close()
