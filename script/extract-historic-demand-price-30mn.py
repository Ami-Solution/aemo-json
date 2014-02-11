import os
import datetime
import csv
import urllib, urllib2
from zipfile import ZipFile
import json

# parameters
url_base = 'http://www.nemweb.com.au'
url_dir = url_base + '/mms.GRAPHS/data/DATA'

states = ["VIC","NSW","SA","QLD","TAS"]
years = ["1999","2000","2001","2002","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014"]
months = ["01","02","03","04","05","06","07","08","09","10","11","12"]

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Store the data from the CSV in a file
out_f = open("../data/nem_historic_demand.csv","w")
out_f.write("region,settlement_date,settlement_time,total_demand,rrp\n")

for state in states:

	for year in years:

		for month in months:
			# Opening u the relevant file for this state
			fn, d = urllib.urlretrieve(url_dir+year+month+"_"+state+"1.CSV")
			#print 'Local copy (spreadsheet) is at: '+fn2
			f = open(fn,'U')

			# It's a CSV file - we extract info in a format ready to be JSONified
			reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)

			for row in reader:
				# First 1 row contains headers
				if reader.line_num < 2:
					continue

				# Subsequent rows contain the information we populate the dictionary with
				# VIC1,"1999/09/01 00:30",5121.98833,16.08,TRADE
				if len(row)>4:
					f_date = row[1].split(" ")[0].replace("\"", "")
					f_time = row[1].split(" ")[1].replace("\"", "")
					f_demand = row[2]
					f_price = row[3]
					# Type: as traded, or projected (irrelevant for historic data)

					# Writing a well-formed CSV line
					out_f.write("\""+state+"\";\""+f_date+"\";\""+f_time+"\";"+f_demand+";"+f_price+"\n")

			f.close()

out_f.close()

# The resulting CSV file can be loaded in PostgreSQL using:

# The destination structure:
# CREATE TABLE nem_demand_price
# (
#  id serial NOT NULL,
#  region character varying(5),
#  settlement_date date,
#  settlement_time time without time zone,
#  total_demand numeric(9,2),
#  rrp numeric(9,2),
#  CONSTRAINT pk_nem_demand_price PRIMARY KEY (id)
#)

# The loading command:
# copy nem_demand_price (region,settlement_date,settlement_time,total_demand,rrp) 
# from '/path/to/file/nem_historic_demand.csv'
# CSV HEADER DELIMITER ';' 
