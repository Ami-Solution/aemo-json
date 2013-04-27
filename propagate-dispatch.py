import os
import urllib,urllib2
import json

auth_token = "app.carbongis.com.au"
url_widget = "http://app.carbongis.com.au:3030/widgets/"
url_json = "http://app.carbongis.com.au/nem2json/dispatch.json"
file_total_values = os.path.join(os.path.dirname(__file__),'graph_hist/total_generation.txt')
file_emission_values = os.path.join(os.path.dirname(__file__),'graph_hist/total_emissions.txt')
file_wind_capacity_factor = os.path.join(os.path.dirname(__file__),'graph_hist/wind_capacity_factor.txt')

total = {'All':0}
total_max = dict(total)
co2_emissions = dict(total) 
fuel_proper_name={'Black Coal':'Black coal','Coal Seam Methane':'Coal seam gas','Coal Tailings':'Coal tailings','Natural Gas':'Natural gas','Kerosene':'Kerosene','Brown Coal':'Brown coal','Diesel':'Diesel','Water':'Hydro','Natural Gas / Fuel Oil':'Natural gas (fuel oil)','Wind':'Wind','Natural Gas / Diesel':'Natural gas (diesel)','Landfill Methane / Landfill Gas':'Landfill gas','Bagasse':'Bagasse','Waste Coal Mine Gas':'Waste coal mine gas','Municipal and Industrial Materials':'Municipal & industrial materials','Sewerage/Waste Water':'Sewerage/waste water','Macadamia Nut Shells':'Macadamia nut shells'}

fn, d = urllib.urlretrieve(url_json)
f = open(fn,'r')
json_data = json.load(f)
f.close()

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def send_json(j,dest):
	j["auth_token"]=auth_token
	data=json.dumps(j)
	#print dest,data
	req = urllib2.Request(url_widget+dest, data)
	response = urllib2.urlopen(req)

def track_value_in_file(v,fn,nb):
	# adding the latest value to the relevant file
	with open(fn, "a") as myfile:
	    myfile.write(str(v)+'\n')

	# reading the file (576 points * 5mn interval = 2 days) into an array of JSON objects {x:time,y:val}
	with open(fn) as f:
	    point_list = list(f.read().splitlines()[-nb:])

	# rewriting these records in the text file
	with open(fn,"w") as f:
	    f.writelines(["%s\n" % item for item in point_list])

	points = []
	idx=1
	for p in point_list:
	        points.append({'x':idx,'y':float(p)})
	        idx = idx + 1
	return points


for s in sorted(json_data.keys()):
	data_array = {}
	data_array["title"]=json_data[s]['station_name']
	if 'qty' in json_data[s]:
		data_array["current"]=json_data[s]['qty']
	data_array["state"]=json_data[s]['region']
	data_array["max"]=json_data[s]['reg_capacity_mw']

	# Send the JSON to the target - only need to perform an update if:
	# 1) there is a quantity to update! (comes from the AEMO realtime data)
	# 2) the station is scheduled (or semi-scheduled) (comes from the AEMO spreadsheet)
	# These 2 statements being equivalent, we choose the easiest to implement
	if 'qty' in json_data[s]:
		print s,json_data[s]['fuel'],json_data[s]['qty']
		send_json(data_array,s)

	# Total for some groupings

	# All generation
	if 'qty' in json_data[s]:
		total['All'] = total['All'] + float(json_data[s]['qty'])
		if 'co2_factor' in json_data[s]:
			if is_number(json_data[s]['co2_factor']):
				co2_emissions['All'] = co2_emissions['All'] + float(json_data[s]['qty']) * float(json_data[s]['co2_factor'])
	if 'reg_capacity_mw' in json_data[s]:
		if is_number(json_data[s]['reg_capacity_mw']):
			total_max['All'] = total_max['All'] + float(json_data[s]['reg_capacity_mw'])

	# By fuel-type
	curr_fuel = json_data[s]['fuel']
	if curr_fuel <>'':
		curr_fuel = fuel_proper_name[curr_fuel]
		if 'qty' in json_data[s]:
			if curr_fuel in total:
				total[curr_fuel] = total[curr_fuel] + float(json_data[s]['qty'])
				if is_number(json_data[s]['reg_capacity_mw']):
					total_max[curr_fuel] = total_max[curr_fuel] + float(json_data[s]['reg_capacity_mw'])
				else:
					print "Nameplate registered capacity for "+s+" is not a numeric"
				if 'co2_factor' in json_data[s]:
					if is_number(json_data[s]['co2_factor']):
						if curr_fuel in co2_emissions:
							co2_emissions[curr_fuel] = co2_emissions[curr_fuel] + float(json_data[s]['qty']) * float(json_data[s]['co2_factor'])
						else:
							co2_emissions[curr_fuel] = float(json_data[s]['qty']) * float(json_data[s]['co2_factor'])
			else:
				total[curr_fuel] = float(json_data[s]['qty'])
				if is_number(json_data[s]['reg_capacity_mw']):
					total_max[curr_fuel] = float(json_data[s]['reg_capacity_mw'])
				else:
					print "Nameplate registered capacity for "+s+" is not a numeric"

				if 'co2_factor' in json_data[s]:
					if is_number(json_data[s]['co2_factor']):
						co2_emissions[curr_fuel] = float(json_data[s]['qty']) * float(json_data[s]['co2_factor'])


share = {}
co2_share = {}
co2_intensity = {}
total_all=total['All']
for f in total:
	if total[f] <> 0.0:
		share[f] = str(round(total[f]/total_all*100,1))
		co2_intensity[f] = str(round(co2_emissions[f]/total[f],3))
	co2_share[f] = str(round(co2_emissions[f]/co2_emissions['All']*100,1))
	total[f] = str(int(round(total[f]))).split('.')[0]
	if total_max.has_key(f):
		total_max[f] = str(round(total_max[f])).split('.')[0]

print "Total dispatched:",total
print "Total capacity:",total_max
print "Fuel share:",share
print "CO2 intensity:",co2_intensity
print "CO2 share",co2_share

# Sending additional request for groupings
##
wind=fuel_proper_name['Wind']
wind_capacity_factor=str(round(float(total[wind])/float(total_max[wind])*100,1))
data_array = {}
data_array["title"]=wind
data_array["value"]=total[wind]
data_array["max"]=total_max[wind]
# Sending the ALL_WIND JSON
send_json(data_array,"ALL_WIND")

black_coal=fuel_proper_name['Black Coal']
data_array = {}
data_array["title"]=black_coal
data_array["value"]=total[black_coal]
data_array["max"]=total_max[black_coal]
# Sending the JSON
send_json(data_array,"ALL_BLACK_COAL")

natural_gas=fuel_proper_name['Natural Gas']
data_array = {}
data_array["title"]=natural_gas
data_array["value"]=total[natural_gas]
data_array["max"]=total_max[natural_gas]
# Sending the JSON
send_json(data_array,"ALL_NATURAL_GAS")

brown_coal=fuel_proper_name['Brown Coal']
data_array = {}
data_array["title"]=brown_coal
data_array["value"]=total[brown_coal]
data_array["max"]=total_max[brown_coal]
# Sending the JSON
send_json(data_array,"ALL_BROWN_COAL")

hydro=fuel_proper_name['Water']
data_array = {}
data_array["title"]=hydro
data_array["value"]=total[hydro]
data_array["max"]=total_max[hydro]
# Sending the JSON
send_json(data_array,"ALL_WATER")

##
data_array = {}
data_array["title"]="Total"
data_array["value"]=total['All']
data_array["max"]=total_max['All']
# Sending the ALL JSON
send_json(data_array,"ALL")

## Lists
# Other fuels should be a dynamic list because different fuels kick in at different times
other_fuel_list=[{"label":fuel_proper_name['Coal Tailings'],"value":total[fuel_proper_name['Coal Tailings']]},{"label":fuel_proper_name['Kerosene'],"value":total[fuel_proper_name['Kerosene']]},{"label":fuel_proper_name['Diesel'],"value":total[fuel_proper_name['Diesel']]},{"label":fuel_proper_name['Natural Gas / Fuel Oil'],"value":total[fuel_proper_name['Natural Gas / Fuel Oil']]},{"label":fuel_proper_name['Natural Gas / Diesel'],"value":total[fuel_proper_name['Natural Gas / Diesel']]}]
sorted_other_fuel_list=sorted(other_fuel_list, key=lambda k: float(k['value']),reverse=True)

# Only keeping the fuels that have a positive, non-null dispatch quantity
pruned_list=[]
for of in sorted_other_fuel_list:
	if float(of["value"]) > 0.0:
		pruned_list.append(of)

data_array = {}
data_array["title"]="Other fuels"
data_array["items"]=pruned_list
# Sending the ALL JSON
send_json(data_array,"ALL_OTHERS")

# CO2 intensities
avg_co2_intensity = co2_intensity['All']
data_array = {}
data_array["title"]="Overall CO2 emissions intensity"
data_array["current"]=avg_co2_intensity
# Sending the ALL JSON
send_json(data_array,"CO2_AVG_INTENSITY")

# Per fuel
co2_intensity_list=[]
co2_intensity.pop('All',None)
for f in co2_intensity:
	if float(co2_intensity[f]) > 0:
		co2_intensity_list.append({"label":str(f),"value":str(co2_intensity[f])})
sorted_co2_intensity=sorted(co2_intensity_list, key=lambda k: float(k['value']),reverse=True)
print sorted_co2_intensity
data_array = {}
data_array["title"]="Carbon emissions intensity by fuel"
data_array["items"]=sorted_co2_intensity
# Sending the ALL JSON
send_json(data_array,"CO2_INTENSITY")


# CO2 contributions
co2_share_list=[]
co2_share.pop('All',None)
for f in co2_share:
	if float(co2_share[f]) > 1:
		co2_share_list.append({"label":str(f),"value":str(co2_share[f])})
sorted_co2_share = sorted(co2_share_list, key=lambda k: float(k['value']),reverse=True)
print sorted_co2_share
data_array = {}
data_array["title"]="Carbon emissions by fuel"
data_array["items"]=sorted_co2_share
# Sending the ALL JSON
send_json(data_array,"CO2_SHARE")


## 

# Sorting the fuels according to their share
fuel_list=[{"label":fuel_proper_name['Coal Seam Methane'],"value":share[fuel_proper_name['Coal Seam Methane']]},{"label":fuel_proper_name['Black Coal'],"value":share[fuel_proper_name['Black Coal']]},{"label":fuel_proper_name['Brown Coal'],"value":share[fuel_proper_name['Brown Coal']]},{"label":fuel_proper_name['Natural Gas'],"value":share[fuel_proper_name['Natural Gas']]},{"label":fuel_proper_name['Water'],"value":share[fuel_proper_name['Water']]},{"label":fuel_proper_name['Wind'],"value":share[fuel_proper_name['Wind']]}]
sorted_fuel_list=sorted(fuel_list, key=lambda k: float(k['value']),reverse=True)

data_array = {}
data_array["title"]="Fuel share"
data_array["items"]=sorted_fuel_list
# Sending the ALL JSON
send_json(data_array,"FUEL_SHARE")

## Graph
pts = track_value_in_file(total['All'],file_total_values,576)
data_array = {}
data_array["title"]="Dispatched"
data_array["points"]=pts
# Sending the ALL JSON
send_json(data_array,"GRAPH_ALL")


pts = track_value_in_file(wind_capacity_factor,file_wind_capacity_factor,576)
data_array = {}
data_array["title"]="Wind capacity factor"
data_array["points"]=pts
# Sending the ALL JSON
send_json(data_array,"GRAPH_WIND_CAPACITY_FACTOR")


# average CO2 intensity
pts = track_value_in_file(avg_co2_intensity,file_emission_values,576)
data_array = {}
data_array["title"]="Carbon emissions intensity"
data_array["points"]=pts
# Sending the ALL JSON
send_json(data_array,"GRAPH_EMISSIONS_INTENSITY") 


# International list of average CO2 intensities
world_avg_co2=[]
world_avg_co2.append({"label":"Australia","value":avg_co2_intensity})

url_json_co2_fr = "http://app.carbongis.com.au/worldco2/fr/co2.json"
fn, d = urllib.urlretrieve(url_json_co2_fr)
f = open(fn,'r')
json_data = json.load(f)
f.close()
world_avg_co2.append({"label":"France","value":str(json_data['co2_intensity'])})

url_json_co2_uk = "http://app.carbongis.com.au/worldco2/uk/co2.json"
fn, d = urllib.urlretrieve(url_json_co2_uk)
f = open(fn,'r')
json_data = json.load(f)
f.close()
world_avg_co2.append({"label":"UK","value":str(json_data['co2_intensity'])})

url_json_co2_ie = "http://app.carbongis.com.au/worldco2/ie/co2.json"
fn, d = urllib.urlretrieve(url_json_co2_ie)
f = open(fn,'r')
json_data = json.load(f)
f.close()
world_avg_co2.append({"label":"Ireland","value":str(json_data['co2_intensity'])})


world_avg_co2=sorted(world_avg_co2, key=lambda k: float(k['value']),reverse=True)
print "World:",world_avg_co2

data_array = {}
data_array["title"]="Carbon emissions intensity by country"
data_array["items"]=world_avg_co2
# Sending the ALL JSON
send_json(data_array,"WORLD_EMISSIONS_INTENSITY")



#u'Black Coal': '11739.47', u'Coal Seam Methane': '304.47', 'All': '23248.7', u'Coal Tailings': '146.0', u'Natural Gas': '1734.14', u'Kerosene': '-0.07', u'Brown Coal': '5259.36', u'Diesel': '0.0', u'Water': '2612.94', u'Natural Gas / Fuel Oil': '121.2', u'Wind': '1151.93', u'Natural Gas / Diesel': '0.0'}
