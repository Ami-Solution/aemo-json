import os
from datetime import datetime,timedelta
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
	#print 'SCADA file is: '+scada_zip_file

	# Get today's date
	i = datetime.now()

	dttm = ll2.split("/")[-1].split("_")[2]
	dto = datetime.strptime(dttm , '%Y%m%d%H%M') + timedelta(hours=1)
	dt = datetime.strftime(dto,'%Y-%m-%d')
	tm = datetime.strftime(dto,'%H:%M')
	#print 'Date/time:'+ dttm, dto, dt, tm, i.day, "=", datetime.strftime(dto,'%d')

	# Only process if the filename is today's and the hour a multiple of 30
	if datetime.strftime(dto,'%d').lstrip("0") == str(i.day) and (datetime.strftime(dto,'%M') == "00" or datetime.strftime(dto,'%M') == "30"):
		last_dto = dto
		# Downloading the SCADA file (zipped)
		fn, d = urllib.urlretrieve(scada_zip_file)
		print 'Local copy (SCADA file) is at: '+fn

		# Uncompressing and parsing the SCADA file
		zf = ZipFile(fn,'r')
		try:
			# Listing the resources in the zip file - there is only 1
			zfnl = zf.namelist()
			#print 'Filename to extract from the archive: '+ zfnl[0]
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
					
					# Building the participant array with sequential quantities
					if info_dict.has_key(duid):
						if duid == "GERMCRK":
							print "GERMCRK:",tm,qty					
						a = info_dict[duid]
						if not info_dict[duid].has_key("qty"):
							info_dict[duid]["qty"]=[[tm,round(qty,2)]]
						else:
							info_dict[duid]["qty"].append([tm,round(qty,2)])
					else:
						if qty <> 0:
							print 'Entry exists in SCADA file but not in generator.csv: '+str(duid)+' (dispatching '+str(round(qty,2))+' MW)'
		finally:
			zf.close()

# We perform a check to make sure all elements are in there
# There was a case of missing element for Diesel generator in SA
#print "Last DTO:",str(last_dto)
correctFactor = 0
if datetime.strftime(last_dto,'%M')=="30":
	correctFactor = 1

for u in info_dict:
	if info_dict[u].has_key("qty"):
		req_nb_entries = int(datetime.strftime(last_dto,'%H'))*2+correctFactor+1
		if len(info_dict[u]["qty"]) < req_nb_entries:
			print 'Missing some elements for participant: '+str(u)
			print 'Current qty dict:'+str(info_dict[u])
			# Corrective action: build an element
			qe_arr = ["00:00","00:30","01:00","01:30","02:00","02:30","03:00","03:30","04:00","04:30","05:00","05:30","06:00","06:30","07:00","07:30","08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00","20:30","21:00","21:30","22:00","22:30","23:00","23:30"]
			qe_arr_adj = qe_arr[:req_nb_entries]
			print "List of required entries:",str(qe_arr_adj)
			qe_pos = 0;
			for qe in qe_arr_adj:
				if len(info_dict[u]["qty"])>qe_pos:
					print 'Reviewing:',str(qe),' against ',str(info_dict[u]["qty"][qe_pos])
					if info_dict[u]["qty"][qe_pos][0] <> qe:
						# Insert the missing element here
						print 'Fixing: '+str(info_dict[u]["qty"][qe_pos][0])
						info_dict[u]["qty"].insert(qe_pos,[qe,0.0])
						#print info_dict[u]["qty"]
					# After correction, moving to the next element
					#qe_pos = qe_pos + 1
				else:
					print "Fixing: "+str(qe)+" (missing element at the end)"
					info_dict[u]["qty"].append([qe,0.0])
					#print info_dict[u]["qty"]
				# After correction, moving to the next element
				qe_pos = qe_pos + 1

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
jf = open('../data/all-dispatch.json','w')
jf.write(json.dumps(info_dict,sort_keys=True))
jf.close()
