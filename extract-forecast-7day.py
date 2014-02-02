import os
import datetime
import csv
import urllib, urllib2
from zipfile import ZipFile
import json

# parameters
url_base = 'http://www.nemweb.com.au'
url_dir = url_base + '/REPORTS/CURRENT/SEVENDAYOUTLOOK_FULL/'

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# extract the last link in the page - it's the name of the latest SCADA file
response = urllib2.urlopen(url_dir)
html = response.read()
ll = html.split('A HREF="')[-2]
ll2 = ll.split('"')[0]
latest_forecast_zip_file = url_base+ll2
print 'Lastest forecast file is: '+latest_forecast_zip_file

# Downloading the latest SCADA file (zipped)
fn, d = urllib.urlretrieve(latest_forecast_zip_file)
#print 'Local copy (SCADA file) is at: '+fn

# Structure to store the data from the CSV
info_dict = {}

# Uncompressing and parsing the SCADA file
zf = ZipFile(fn,'r')
try:
	# Listing the resources in the zip file - there is only 1
	zfnl = zf.namelist()
	print 'Filename to extract from the archive: '+ zfnl[0]
	f = zf.open(zfnl[0])
	# It's a CSV file - we extract info in a format ready to be JSONified
	reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)

	for row in reader:
		# First 2 rows contain headers
		if reader.line_num < 3:
			continue
		# Subsequent rows contain the information we populate the dictionary with
		# D,SEVENDAYOUTLOOK,PEAK,1,NSW1,"2014/02/03 00:00:00",6790,11044,-2592.87,6846.87,"2014/02/03 00:30:00"
		if len(row)>6:
			state = row[4].replace("1", "")
			f_date = row[10].split(" ")[0].replace("\"", "")
			f_time = row[10].split(" ")[1].replace("\"", "")
			f_scheduled_demand = row[6]
			f_scheduled_capacity = row[7]
			f_net_interchange = row[8]
			f_scheduled_reserve = row[9]

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
				"demand": f_scheduled_demand,
				"capacity": f_scheduled_capacity,
				"interchange": f_net_interchange,
				"reserve": f_scheduled_reserve
			}

finally:
	zf.close()

f.close()

# Outputting the dictionary for RTEM application
jf = open(os.path.join(os.path.dirname(__file__),'aemo-forecast-7days.json'),'w')
jf.write(json.dumps(info_dict,sort_keys=True, indent=4))
jf.close()
