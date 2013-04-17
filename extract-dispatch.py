import os
import datetime
import csv
import urllib, urllib2
from zipfile import ZipFile
import json

# parameters
url_base = 'http://www.nemweb.com.au'
url_dir = url_base + '/REPORTS/CURRENT/Dispatch_SCADA/'
response = urllib2.urlopen(url_dir)

# Extracting the last link in the page - it's the name of the latest SCADA file
html = response.read()
ll = html.split('A HREF="')[-2]
ll2 = ll.split('"')[0]
latest_scada_zip_file = url_base+ll2
print 'Lastest SCADA file is: '+latest_scada_zip_file

# Downloading the latest SCADA file (zipped)
fn, d = urllib.urlretrieve(latest_scada_zip_file)
#print 'Local copy (SCADA file) is at: '+fn

# Opening the reference file that contains static information about the generators
url_spreadsheet = 'https://docs.google.com/spreadsheet/pub?key=0Asxkb_brURPldDhhSmp2ZUNiSWZDVUlnaXFKQVNfVFE&single=true&gid=5&output=csv'
fn2, d2 = urllib.urlretrieve(url_spreadsheet)
#print 'Local copy (spreadsheet) is at: '+fn2
f2 = open(fn2,'r')
reader2 = csv.reader(f2, delimiter=',', quoting=csv.QUOTE_NONE)

# Populating dictionaries for future groupings
info_dict = {}

for row in reader2:
	if reader2.line_num <2:
		continue
	if len(row)>19:
		if len(row[2])<2 or len(row[6])<2 or len(row[7])<2 or len(row[8])<2 or len(row[9])<2:
			print "Unknown characteristic(s) for "+str(row[13])+" on line "+str(reader2.line_num)
		else:
			current_info={}
			current_info["participant"]=row[0]
			current_info["station_name"]=row[1]
			current_info["region"]=row[2][:-1]
			current_info["fuel"]=row[7]
			current_info["technology"]=row[9]
			current_info["reg_capacity_mw"]=row[14]
			current_info["co2_factor"]=row[19]
			current_info["lon"]=row[17]
			current_info["lat"]=row[18]
			info_dict[row[13]] = dict(current_info)

f2.close()

# Uncompressing and parsing the SCADA file
zf = ZipFile(fn,'r')
try:
	# Listing the resources in the zip file - there is only 1
	zfnl = zf.namelist()
	print 'Filename to extract from the archive: '+ zfnl[0]
	f = zf.open(zfnl[0])
	# It's a CSV file - we only extract the relevant lines (=HAZELWOOD) 
	# and columns (dispatcher name in column 5 and quantity dispatched in column 6)
	reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)

	for row in reader:
		# First 2 rows contain headers
		if reader.line_num < 3:
			continue
		# Subsequent rows contain the information we populate the dictionary with
		if len(row)>6:
			duid = row[5]
			qty = float(row[6])
			
			# Building the state dictionary with accumulated quantity
			if info_dict.has_key(duid):
				a = info_dict[duid]
				info_dict[duid]["qty"]=str(round(qty,2))
			else:
				print 'No information available for DUID: '+str(duid)
finally:
	zf.close()

f.close()


# Outputting the dictionary for RTEM application
jf = open(os.path.join(os.path.dirname(__file__),'dispatch.json'),'w')
jf.write(json.dumps(info_dict,sort_keys=True, indent=4))
jf.close()
