import os
import datetime
import csv
import urllib, urllib2
from zipfile import ZipFile
import json

# parameters
rootdir = '/home/hsenot/Data/AEMO/PUBLIC_PRICES'

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Store the data from the CSV in a file
out_f = open("../data/nem_historic_prices.csv","w")
out_f.write("dort,aemo,settlement_date,settlement_time,region,rrp\n")


for subdir, dirs, files in os.walk(rootdir):
	files.sort()
	for file in files:
		# Filename
		zf = ZipFile(subdir+'/'+file,'r')

		# Listing the resources in the zip file - there is only 1
		zfnl = zf.namelist()
		print 'Filename to extract from the archive: '+ zfnl[0]
		f = zf.open(zfnl[0])

		# It's a CSV file - we extract info in a format ready to be JSONified
		reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)
		zf.close()

		for row in reader:
			if len(row)>1:
				# Data rows identified with D flag in first column
				if row[0] == "D":
					# Selection of the right columns to consider
					f_dort = row[1][0:1]
					f_aemo = row[3]
					f_date = row[4].split(" ")[0].replace("\"", "")
					f_time = row[4].split(" ")[1].replace("\"", "")
					f_region = row[6][:-1]

					# The RRP column might be in position 7 or 8
					if f_dort == "D":
						f_price = row[8]
					else:
						f_price = row[7]

					# Writing a well-formed CSV line
					out_f.write("\""+f_dort+"\";"+f_aemo+";\""+f_date+"\";\""+f_time+"\";\""+f_region+"\";"+f_price+"\n")

		f.close()

out_f.close()

# The resulting CSV file can be loaded in PostgreSQL using:

# The destination structure:
# CREATE TABLE nem_public_price
# (
#  id serial NOT NULL,
#  dort character(1),
#  aemo smallint,
#  settlement_date date,
#  settlement_time time without time zone,
#  region character varying(5),
#  rrp numeric(9,2),
#  CONSTRAINT pk_nem_public_price PRIMARY KEY (id)
# )

# The loading command:
# copy nem_public_price (dort,aemo,settlement_date,settlement_time,region,rrp) 
# from '/var/lib/tomcat6/webapps/empower.me/data/aemo-json/data/nem_historic_prices.csv'
# CSV HEADER DELIMITER ';' 

# A reduced table that only has the 30mn (final) spot price:
#
# drop table nem_public_price_mini cascade;
#
# create table nem_public_price_mini as
# select 
#	id, region, settlement_date, settlement_time,rrp
# from 
#	nem_public_price 
# where 
#	dort='T' and aemo=1
# order by
#	region, settlement_date, settlement_time