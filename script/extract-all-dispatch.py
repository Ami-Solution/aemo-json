import os
import datetime
import csv
import urllib, urllib2
from zipfile import ZipFile
import json
from bs4 import BeautifulSoup

# parameters
url_csv_generator = 'https://raw.github.com/hsenot/aemo/master/out/generator.csv'
url_csv_co2 = 'https://raw.github.com/hsenot/aemo/master/out/co2.csv' 
url_base = 'http://www.nemweb.com.au'
url_dir = url_base + '/REPORTS/CURRENT/Dispatch_SCADA/'

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Static information about the generators
fn2, d2 = urllib.urlretrieve(url_csv_generator)
#print 'Local copy (spreadsheet) is at: '+fn2
f2 = open(fn2,'U')
reader2 = csv.reader(f2, delimiter=',', quoting=csv.QUOTE_NONE)

# Populating dictionaries for future groupings
info_dict = {}

for row in reader2:
	# Skipping first line, which contains the headers
	if reader2.line_num <2:
		continue
	# Considering only stations which have a proper dispatch ID (i.e. not '-')
	if row:
		if len(row[13])>1:
			if is_number(row[14]):
				# Building the attributes dictionary (names and values) for this station
				current_info={}
				current_info["participant"]=row[0]
				current_info["station_name"]=row[1]
				current_info["region"]=row[2][:-1]
				current_info["fuel"]=row[7]
				current_info["technology"]=row[9]
				current_info["class"]=row[5]
				current_info["reg_capacity_mw"]=row[14]
				info_dict[row[13]] = dict(current_info)
			else:
				if row[12] <> 'Y':
					print "Nameplate is not a numeric for "+row[13]

f2.close()

# extract the links in the HTML page
response = urllib2.urlopen(url_dir)
html = response.read()
soup = BeautifulSoup(html)

# Now looping thru all "a href" links and extract the data
# Note: skipping the first a link (it is a link to the parent directory, not a zipped SCADA file)
for a_tag in soup.find_all('a')[1:]:
	ll2 = a_tag.get('href')
	scada_zip_file = url_base+ll2
	print 'SCADA file is: '+scada_zip_file

	# Get today's date
	i = datetime.datetime.now()

	dttm = ll2.split("/")[-1].split("_")[2]
	dt = dttm[:4]+"-"+dttm[4:6]+"-"+dttm[6:8]
	tm = dttm[8:10]+":"+dttm[10:]
	#print 'Date/time:'+ dttm, dt, tm, i.day

	# Only process if the filename is a multiple of 30!
	if dttm[6:8] == str(i.day) and (dttm[10:] == "00" or dttm[10:] == "30"):
		# Downloading the SCADA file (zipped)
		fn, d = urllib.urlretrieve(scada_zip_file)
		print 'Local copy (SCADA file) is at: '+fn

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
						if not info_dict[duid].has_key("qty"):
							info_dict[duid]["qty"]=[[dt+" "+tm,round(qty,2)]]
						else:
							info_dict[duid]["qty"].append([dt+" "+tm,round(qty,2)])
					else:
						if qty <> 0:
							print 'Entry exists in SCADA file but not in generator.csv: '+str(duid)+' (dispatching '+str(round(qty,2))+' MW)'
		finally:
			zf.close()

# Scanning entries in info_dict that have no dispatch in SCADA file (i.e. that have no dispatch qty)
for g in sorted(info_dict.keys()):
	if not info_dict[g].has_key("qty") and info_dict[g]["class"] <> "Non-Scheduled":
		print 'Entry '+str(g)+' ('+str(info_dict[g]["class"])+') has no dispatched quantity'

# Adding the co2 information
# Opening the reference file that contains static information about the emission factors
fn3, d3 = urllib.urlretrieve(url_csv_co2)
#print 'Local copy (spreadsheet) is at: '+fn2
f3 = open(fn3,'U')
reader3 = csv.reader(f3, delimiter=',', quoting=csv.QUOTE_NONE)

for row in reader3:
        # Skipping first line, which contains the headers
        if reader3.line_num <2:
                continue
        # Considering only stations which have a proper dispatch ID (i.e. not '-')
        if len(row[1])>0:
		duid = row[0]
		co2_factor = row[1]

		if info_dict.has_key(duid):
                	a = info_dict[duid]
                        info_dict[duid]["co2_factor"]=co2_factor
                else:
                	print 'Entry exists in co2.out but not in generator.csv: '+str(duid)

# Scanning entries in info_dict that have no CO2 information (i.e. no co2_factor)
for g in sorted(info_dict.keys()):
        if not info_dict[g].has_key("co2_factor"):
		if info_dict[g]["fuel"] <> "Wind" and info_dict[g]["fuel"] <> "Water" and info_dict[g]["class"] <> "Non-Scheduled":
                	print 'Entry '+str(g)+' ('+str(info_dict[g]["reg_capacity_mw"])+'MW of '+str(info_dict[g]["fuel"])+') has no CO2 emission factor'


# Outputting the dictionary for RTEM application
jf = open('../data/dispatch.json','w')
jf.write(json.dumps(info_dict,sort_keys=True))
jf.close()
