import os
import urllib,urllib2
import json

auth_token = "app.carbongis.com.au"
url_widget = "http://app.carbongis.com.au:3030/widgets/"
url_json = "http://app.carbongis.com.au/nem2json/dispatch.json"
file_total_values = os.path.join(os.path.dirname(__file__),'total.txt')

total = {'All':0}
total_max = dict(total)

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
	if 'reg_capacity_mw' in json_data[s]:
		if is_number(json_data[s]['reg_capacity_mw']):
			total_max['All'] = total_max['All'] + float(json_data[s]['reg_capacity_mw'])

	# By fuel-type
	curr_fuel = json_data[s]['fuel']
	if curr_fuel <>'':
		if 'qty' in json_data[s]:
			if curr_fuel in total:
				total[curr_fuel] = total[curr_fuel] + float(json_data[s]['qty'])
				total_max[curr_fuel] = total_max[curr_fuel] + float(json_data[s]['reg_capacity_mw'])
			else:
				total[curr_fuel] = float(json_data[s]['qty'])
				total_max[curr_fuel] = float(json_data[s]['reg_capacity_mw'])


share = {}
total_all=total['All']
for f in total:
	if total_max[f] <> 0:
		share[f] = str(round(total[f]/total_all*100,1))
	total[f] = str(int(round(total[f]))).split('.')[0]
	total_max[f] = str(round(total_max[f])).split('.')[0]

print "Total dispatched:",total
print "Total capacity:",total_max
print "Fuel share:",share

# Sending additional request for groupings
##
data_array = {}
data_array["title"]="Wind"
data_array["value"]=total['Wind']
data_array["max"]=total_max['Wind']
# Sending the ALL_WIND JSON
send_json(data_array,"ALL_WIND")

data_array = {}
data_array["title"]="Black coal"
data_array["value"]=total['Black Coal']
data_array["max"]=total_max['Black Coal']
# Sending the JSON
send_json(data_array,"ALL_BLACK_COAL")

data_array = {}
data_array["title"]="Natural gas"
data_array["value"]=total['Natural Gas']
data_array["max"]=total_max['Natural Gas']
# Sending the JSON
send_json(data_array,"ALL_NATURAL_GAS")

data_array = {}
data_array["title"]="Brown coal"
data_array["value"]=total['Brown Coal']
data_array["max"]=total_max['Brown Coal']
# Sending the JSON
send_json(data_array,"ALL_BROWN_COAL")

data_array = {}
data_array["title"]="Hydro"
data_array["value"]=total['Water']
data_array["max"]=total_max['Water']
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
other_fuel_list=[{"label":"Coal tailings","value":total['Coal Tailings']},{"label":"Kerosene","value":total['Kerosene']},{"label":"Diesel","value":total['Diesel']},{"label":"Natural gas / fuel oil","value":total['Natural Gas / Fuel Oil']},{"label":"Natural gas / diesel","value":total['Natural Gas / Diesel']}]
sorted_other_fuel_list=sorted(other_fuel_list, key=lambda k: float(k['value']),reverse=True)

# Only keeping the fuels that have a positive, non-null dispatch quantity
pruned_list=[]
for of in sorted_other_fuel_list:
	if float(of["value"]) > 0.0:
		pruned_list.append(of)

data_array = {}
data_array["title"]="Other fuels (MW)"
data_array["items"]=pruned_list
# Sending the ALL JSON
send_json(data_array,"ALL_OTHERS")

## 

# Sorting the fuels according to their share
fuel_list=[{"label":"Coal seam gas","value":share['Coal Seam Methane']},{"label":'Black coal',"value":share['Black Coal']},{"label":'Brown coal',"value":share['Brown Coal']},{"label":'Natural gas',"value":share['Natural Gas']},{"label":'Hydro',"value":share['Water']},{"label":'Wind',"value":share['Wind']}]
sorted_fuel_list=sorted(fuel_list, key=lambda k: float(k['value']),reverse=True)

data_array = {}
data_array["title"]="Fuel share"
data_array["items"]=sorted_fuel_list
# Sending the ALL JSON
send_json(data_array,"FUEL_SHARE")

## Graph
# adding the latest value to the relevant file
with open(file_total_values, "a") as myfile:
    myfile.write(str(int(float(total['All'])))+'\n')

# reading the file (576 points * 5mn interval = 2 days) into an array of JSON objects {x:time,y:val}
with open(file_total_values) as f:
    point_list = list(f.read().splitlines()[-576:])

points = [] 
idx=1
for p in point_list:
	points.append({'x':idx,'y':int(p)})
	idx = idx + 1

data_array = {}
data_array["title"]="Dispatched (MW)"
data_array["points"]=points
# Sending the ALL JSON
send_json(data_array,"GRAPH_ALL")


#{u'Black Coal': '11739.47', u'Coal Seam Methane': '304.47', 'All': '23248.7', u'Coal Tailings': '146.0', u'Natural Gas': '1734.14', u'Kerosene': '-0.07', u'Brown Coal': '5259.36', u'Diesel': '0.0', u'Water': '2612.94', u'Natural Gas / Fuel Oil': '121.2', u'Wind': '1151.93', u'Natural Gas / Diesel': '0.0'}
