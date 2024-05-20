from datetime import datetime,timedelta
import math
import sys
import os

import numpy as np
from netCDF4 import Dataset as netcdf

class Station:
    lat = -1
    lon = -1
    alt = -1
    ztds = []
    dates = []
    def __init__(self, name):
        self.name = name

class Point:
    def __init__(self,altitude,date,temperature,pressure,closest_station):
        self.alt = altitude
        self.date = date
        self.temp = temperature
        self.press = pressure
        self.closest_station = closest_station

class Result:
    def __init__(self,time,ztd,temp,pressure,zhd,zwd,iwv,station):
        self.time = time
        self.ztd = ztd
        self.temp = temp
        self.press = pressure
        self.zhd = zhd
        self.zwd = zwd
        self.iwv = iwv
        self.station_name = station.name
        self.lat = station.lat
        self.lon = station.lon
        self.alt = station.alt
        
# assumes time is datetime object
def time_into_epoch(time):
    day = time.timetuple().tm_yday
    seconds = time.hour*3600 + time.minute * 60 + time.second
    year = time.year
    return "{}:{}:{}".format(year,day,seconds)

def read_met_from_wrf(files,stations):
    points = []
    for file in files:
        # Open the NetCDF file
        ncfile = netcdf(file)

        # Extract the variables
        time = ncfile.variables['Times']
        temp = ncfile.variables['T2']
        pres = ncfile.variables['PSFC']
        lat = ncfile.variables['XLAT']
        lon = ncfile.variables['XLONG']

        # find squared distance of every point on grid
        for station in stations:
            dist_sq = (lat[0][:]-station.lat)**2 + (lon[0][:]-station.lon)**2
            # 1D index of minimum dist_sq element
            minindex_flattened = dist_sq.argmin()
            # Get 2D index for latvals and lonvals arrays from 1D index
            i,j = np.unravel_index(minindex_flattened, lat[0][:].shape)

            date = datetime.strptime(time[0].tobytes().decode("utf-8"),"%Y-%m-%d_%H:%M:%S")
            temperature = temp[0][i][j]-273.15
            pressure = pres[0][i][j]/100
            alt = ncfile.variables["HGT"][0][i][j]
            points.append(Point(alt,date,temperature,pressure,station.name))

        ncfile.close()

    return points

def read_stations_latlon(file,stations, add_all = False):
    line = file.readline()
    # assuming the line that is read is the first line of +SITE/ID
    # *STATION__ PT __DOMES__ T _STATION DESCRIPTION__ _LONGITUDE _LATITUDE_ _HGT_ELI_ _HGT_MSL_
    # => [*STATION__, PT, __DOMES__, T,_STATION DESCRIPTION__, _LONGITUDE, _LATITUDE_, _HGT_ELI_, _HGT_MSL_]
    cols = line.split()
    name_index = -1
    lon_index = -1
    lat_index = -1
    alt_index = -1
    for i in range(len(cols)):
        if 'LONGITUDE' in cols[i] and lon_index == -1:
            lon_index = i
        if 'LATITUDE' in cols[i] and lat_index == -1:
            lat_index = i
        if 'HGT_MSL' in cols[i] and alt_index == -1:
            alt_index = i
        if 'STATION' in cols[i] and name_index == -1:
            name_index = i

    if name_index == -1 or lat_index == -1 or lon_index == -1 or alt_index == -1:
        print("Couldn't find station name, longitude, latitude or altitude in snx file...")
        file.close()
        sys.exit(1)

    line = file.readline()
    while not line.startswith('-SITE/ID'):
        line = line.split()

        # TODO Refactor
        # if column is missing and assuming that lon,lat,alt are at end
        diff = len(cols) - len(line)

        station_name = line[name_index].strip()
        if add_all and stations.get(station_name) == None:
            stations[station_name] = Station(station_name)

        if stations.get(station_name) != None: 
            stations[station_name].lon = float(line[lon_index-diff])
            stations[station_name].lat = float(line[lat_index-diff])
            stations[station_name].alt = float(line[alt_index-diff])
        line = file.readline()

    
    not_found_stations = []
    for station_name in stations:
        if stations[station_name].lon == -1 or stations[station_name].lat == -1 or stations[station_name].alt == -1:
            not_found_stations.append(station_name)
            print("Station",station_name,"not found, removing...")
    
    for station_name in not_found_stations:
        stations.pop(station_name,None)


def read_trop_solution(file,stations):
    line = file.readline()
    cols = line.split()
    epoch_index = -1
    ztd_index = -1
    for i in range(len(cols)):
        if 'EPOCH' in cols[i]:
            epoch_index = i
        if 'TROTOT' in cols[i]:
            ztd_index = i

    if epoch_index == -1 or ztd_index == -1:
        print("Couldn't find time or ztd in snx file...") 
        file.close()
        sys.exit(1)

    while not line.startswith('-TROP/SOLUTION'):
        line = line.split()
        station_name = line[0].strip()

        if stations.get(station_name) != None:
            date = line[epoch_index].split(':')

            # Calculate epoch into datetime
            day_in_seconds = float(date[2])
            day_in_hours = day_in_seconds/3600
            hours = math.floor(day_in_hours)
            minutes_full = (day_in_hours-hours)*60
            minutes = round(minutes_full,3)
            seconds = round((minutes_full-minutes)*60,3)
            actual_date = datetime(int(date[0]),1,1) + timedelta(int(date[1])-1)
            actual_date += timedelta(0,seconds,0,0,minutes,hours,0)

            # add data to station
            stations[station_name].dates.append(actual_date)
            stations[station_name].ztds.append(float(line[ztd_index])/1000)

        line = file.readline()


def read_gps_from_snx(file,station_names):
    snx = open(file,'r')
    stations = {}
    for station_name in station_names:
        stations[station_name] = Station(station_name)

    while True:
        line = snx.readline()
        if line == '':
            break

        if line.startswith("+TROP/SOLUTION"):
            read_trop_solution(snx,stations)
        elif line.startswith("+SITE/ID"):
            read_stations_latlon(snx,stations,len(stations) == 0)
            
    snx.close()
    return list(stations.values())


argv = {
    "snx-file": '', #one
    "wrf-file": '', #multiple
    "station": '', #multiple, optional
    "o": '', #optional
}
# cli arguments
if len(sys.argv) == 1:
    print("Usage: python3 iwvcalc.py --snx-file snx_file --wrf-file wrf_file --station station [--o output_file]")
    sys.exit(1)
for i in range(1,len(sys.argv),2):
    if len(sys.argv) < i+1:
        print("Invalid arguments. Exiting...")
        sys.exit(1)
    argv[sys.argv[i][2:]] = sys.argv[i+1]

if ',' in argv["station"]:
    argv["station"] = argv["station"].split(',')
elif argv["station"] == '':
    argv["station"] = []
else:
    argv["station"] = [argv["station"]]

if ',' in argv["wrf-file"]:
    argv["wrf-file"] = argv["wrf-file"].split(',')
else:
    if os.path.isdir(argv["wrf-file"]):
        path = argv["wrf-file"]
        argv["wrf-file"] = []
        for file in os.listdir(path):
            argv["wrf-file"].append(path+"/"+file)
    else:
        argv["wrf-file"] = [argv["wrf-file"]]

for file in argv["wrf-file"]:
    if not os.path.isfile(file):
        print(file,"doesn't exist.")
        sys.exit(1)

if not os.path.isfile(argv['snx-file']):
    print(file,"doesn't exist.")
    sys.exit(1)

if argv['snx-file'] == '' or len(argv['wrf-file']) == 0:
    print("Missing required arguments. Exiting...")
    sys.exit(1)


try:
    stations = read_gps_from_snx(argv["snx-file"],argv["station"])
    if len(stations) == 0:
        print("No stations found. Exiting...")
        sys.exit(1)
    # print("Stations len:",len(stations))
    # for station in stations:
    #     print(station.lon)

    #met
    points = read_met_from_wrf(argv['wrf-file'],stations)
    if len(points) == 0:
       print("No data found from wrf file. Exiting...")
       sys.exit(1)
    
    # print("Points len:",len(points))
    points = sorted(points,key=lambda x: x.date)
    # for point in points:
    #     print(point.alt)

    #average datetime intervals

    results = {}
    for station in stations:
        t = points[0].date
        step = timedelta(0,0,0,0,5,0,0) # 5 mins
        met = []
        gps = []
        point_alt = -1

        while t <= points[-1].date + step:
            celc = 0
            hpa = 0
            count = 0
            for point in points:
                # if between step time 
                if point.closest_station == station.name and point.date > t-step/2 and point.date < t+step/2:
                    celc += point.temp
                    hpa += point.press
                    count += 1
                    point_alt = point.alt

            # take average
            if count > 0:
                met.append([t,celc/count,hpa/count])
            
            ztd = 0
            count = 0
            for i in range(len(station.dates)):
                # if between step time 
                if station.dates[i] > t-step/2 and station.dates[i] < t+step/2:
                    ztd += station.ztds[i]
                    count += 1
            
            # take average
            if count > 0:
                gps.append([t,ztd/count])

            t += step

        #met[i][0] = time
        #met[i][1] = temp
        #met[i][2] = pressure

        #gps[i][0] = time
        #gps[i][1] = ztd

        # datetime matching
        gpsmet = []
        for i in range(len(gps)):
            for j in range(len(met)):
                # gps time matches met time
                # i.e. 14:00 for both, 14:05 for both, etc...
                if gps[i][0] == met[j][0]:
                    # [time, ztd, temp, pressure,zhd,zwd,iwv,station id, source gnss id, source met id]
                    gpsmet.append([gps[i][0],gps[i][1],met[j][1],met[j][2]])

        if len(gpsmet) == 0:
            print("No matching times found. Exiting...")
            sys.exit(1) 
        #gpsmet[i][0] = time
        #gpsmet[i][1] = ztd
        #gpsmet[i][2] = temp
        #gpsmet[i][3] = pressure

        # IWV Calcs
        press = 1013.25 * ( - ( 1 - 0.0000226 * point_alt ) ** 5.225 + ( 1 - 0.0000226 * station.lat ) ** 5.225 );  
        g = -9.806 #%m/s^2
        M = 0.0289644 #%kg/mol
        R = 8.31432 #%N·m/(mol·K)
        T = 288.15 #%K
        L = -0.0065 #%Temperature Lapse Rate K/m

        temp = - L * (point_alt - station.alt)
        c0 = 0.0000024
        c1 = 0.0022768
        c2 = 0.00266
        c3 = 0.00028

        ef = []
        Tm = []
        ak = []

        for i in range(len(gpsmet)):
            gpsmet[i][2] += temp
            T = gpsmet[i][2] + 273.15

            gpsmet[i][3] *= (T/(T+L*(point_alt-station.alt)))**(g*M/(R*L))

            ef.append(1-c2*math.cos(2*(station.lat*math.pi)/180) - c3*station.alt/1000)

            Tm.append(70.2 + 0.72 * (gpsmet[i][2]+273.16))

            ak.append((10.0**5)/(461.51*(((3.776*(10.0**5))/Tm[-1] + 22))))

            gpsmet[i].append((c1*gpsmet[i][3])/ef[-1]) # zhd

            gpsmet[i].append(gpsmet[i][1] - gpsmet[i][-1]) # zwd

            gpsmet[i].append(ak[-1]*gpsmet[i][-1]*1000) # iwv

            # station latitude
            gpsmet[i].append(station.lat)
            # station altitude
            gpsmet[i].append(station.alt)
            # station longitude
            gpsmet[i].append(station.lon)

            #TODO Refactor
            if results.get(station.name,None) == None:
                results[station.name] = []
            results[station.name].append(Result(gpsmet[i][0],gpsmet[i][1],gpsmet[i][2],gpsmet[i][3],gpsmet[i][4],gpsmet[i][5],gpsmet[i][6],station))

        #gpsmet[i][0] = time
        #gpsmet[i][1] = ztd
        #gpsmet[i][2] = temp
        #gpsmet[i][3] = pressure
        #gpsmet[i][4] = zhd
        #gpsmet[i][5] = zwd
        #gpsmet[i][6] = iwv
        #gpsmet[i][7] = station_latitude
        #gpsmet[i][8] = station_altitude
        #gpsmet[i][9] = station_longitude

    # TODO Save in troposinex format
    if argv['o'] != '':
        with open(argv['o'], 'w') as troposinex:
            troposinex.write('''%=TRO
*---------------------------------------------------------------------------- 
+FILE/REFERENCE 
*INFO_TYPE_____ INFO______________________________ 
 DESCRIPTION	SUGAC 
 OUTPUT			SUGAC 
 CONTACT		GUEROVA 
 SOFTWARE		WRFv3.7.1 
 INPUT			NWM 
 VERSION NUMBER	001 
-FILE/REFERENCE 
*---------------------------------------------------------------------------- 
+TROP/DESCRIPTION 
*_____KEYWORD_______        __VALUE(S)________________
 REFRACTIVITY COEFFICIENTS 	77.60 70.40 373900.0
 TROPO SAMPLING INTERVAL 	3600
 TIME SYSTEM 			    UTC
 TROPO PARAMETER NAMES		IWV PRESS TEMDRY TRODRY TROTOT TROWET
 TROPO PARAMETER UNITS		  1     1      1  1e+03  1e+03  1e+03
 TROPO PARAMETER WIDTH		  6     6      6      6      6      6
-TROP/DESCRIPTION 
*---------------------------------------------------------------------------- 
+SITE/ID 
*STATION__ _LONGITUDE _LATITUDE_ _HGT_MSL_''')
            for station in stations:
                troposinex.write('\n {name:>9} {longit:>10.6f} {latt:>10.6f} {alt:>9.3f}'
					.format(
					name     = station.name,
					longit   = station.lon,
					latt     = station.lat,
					alt      = station.alt
				))
            troposinex.write('''
-SITE/ID
*----------------------------------------------------------------------------
+SITE/COORDINATES
-SITE/COORDINATES
*----------------------------------------------------------------------------
+TROP/SOLUTION
*STATION__ ____EPOCH_____ _IWV_ __PRESS TEMPDRY TRODRY TROTOT TROWET''')
# FIELD NAMES:
# Station = station name
# Epoch   = timestamp YY:DDD:SSSSS
# IWV     = Integrated water vapour, [kg/m^2]
# PRESS   = Pressure, [Pa]
# TEMPDRY = Dry temperature temp, [K]
# TRODRY  = zhd_mm, [mm]
# TROTOT  = ZTD_mm, [mm]
# TROWET  = ZWD_mm, [mm]
            for station in stations:
                for result in results[station.name]:
                    troposinex.write('\n {name:9s} {epoch:>7s} {IWV:>5.2f} {press:>7.2f} {temp:>7.1f} {TRODRY:>6.1f} {TROTOT:>6.1f} {TROWET:>6.1f}'
                        .format(
                        name     = result.station_name,
                        epoch    = time_into_epoch(result.time),
                        IWV      = result.iwv,
                        press    = result.press,
                        temp     = result.temp+273.15,
                        TRODRY   = result.zhd,
                        TROTOT   = result.ztd,
                        TROWET   = result.zwd
                    ))
            troposinex.write('''\n-TROP/SOLUTION
%=ENDTRO
''')
            troposinex.close()
    else:
        print('station,time,ztd,temp,pressure,zhd,zwd,iwv,station_latitude,station_altitude,station_longitude')
        for station in stations:
            for result in results[station.name]:
                print(result.station_name,end=' ')
                print(result.time,end=' ')
                print(result.ztd,end=' ')
                print(result.temp,end=' ')
                print(result.press,end=' ')
                print(result.zhd,end=' ')
                print(result.zwd,end=' ')
                print(result.iwv,end=' ')
                print(station.lat,end=' ')
                print(station.alt,end=' ')
                print(station.lon)

except FileNotFoundError as e:
    print("File not found: {0}. Exiting...".format(e.filename))
    sys.exit(1)
