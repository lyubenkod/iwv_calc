from datetime import datetime,timedelta
import math
import sys

import numpy as np
from netCDF4 import Dataset as netcdf

def read_met_from_wrf(file,station_id,lonpt,latpt):
    # Open the NetCDF file
    ncfile = netcdf(file)

    # Extract the variables
    time = ncfile.variables['Times']
    temp = ncfile.variables['T2']
    pres = ncfile.variables['PSFC']
    lat = ncfile.variables['XLAT']
    lon = ncfile.variables['XLONG']

    # find squared distance of every point on grid
    dist_sq = (lat[0][:]-latpt)**2 + (lon[0][:]-lonpt)**2
    # 1D index of minimum dist_sq element
    minindex_flattened = dist_sq.argmin()
    # Get 2D index for latvals and lonvals arrays from 1D index
    i,j = np.unravel_index(minindex_flattened, lat[0][:].shape)

    date = datetime.strptime(time[0].tobytes().decode("utf-8"),"%Y-%m-%d_%H:%M:%S")
    temperature = temp[0][i][j]-273.15
    pressure = pres[0][i][j]/100

    ncfile.close()

    return [station_id,date,temperature,pressure]

def read_stations_latlon(file,station):
    lat,lon = -1, -1
    line = file.readline()
    # assuming the line that is read is the first line of +SITE/ID
    # *STATION__ PT __DOMES__ T _STATION DESCRIPTION__ _LONGITUDE _LATITUDE_ _HGT_ELI_ _HGT_MSL_
    # => [STATION__, PT, __DOMES__, T, STATION DESCRIPTION__, _LONGITUDE, _LATITUDE_, _HGT_ELI_, _HGT_MSL_]
    cols = line.split()
    lensum = 0
    lon_location = -1
    for col in cols:
        if 'LONGITUDE' in col:
            lon_location = lensum + 1
            break
        lensum += len(col) + 1

    lat_location = -1
    lensum = 0
    for col in cols:
        if 'LATITUDE' in col:
            lat_location = lensum + 1
            break
        lensum += len(col) + 1

    while not line.startswith('-SITE/ID'):
        if line.startswith(" "+station) and lat_location != -1 and lon_location != -1:
            lon,lat = (float(line[lon_location:].split()[0]),float(line[lat_location:].split()[0]))

        line = file.readline()
    return lon,lat


def read_trop_solution(file,station):
    result = []
    line = file.readline()
    while not line.startswith('-TROP/SOLUTION'):
        if line.startswith(" "+station):
            formatted = line.strip().split(' ')[:3]
            # Reading TROTOT
            date = formatted[1].split(':')
            day_in_seconds = float(date[2])

            day_in_hours = day_in_seconds/3600
            hours = math.floor(day_in_hours)
            minutes_full = (day_in_hours-hours)*60
            minutes = round(minutes_full,3)
            seconds = round((minutes_full-minutes)*60,3)
            actual_date = datetime(int(date[0]),1,1) + timedelta(int(date[1])-1)
            actual_date += timedelta(0,seconds,0,0,minutes,hours,0)

            formatted[1] = actual_date
            formatted[2] = float(formatted[2])/1000

            result.append(formatted)

        line = file.readline()
    return result


def read_gps_from_snx(file,station):
    gps = []
    snx = open(file,'r')
    lon,lat = -1, -1

    while True:
        line = snx.readline()
        if line == '':
            break

        if line.startswith("+TROP/SOLUTION"):
            gps = read_trop_solution(snx,station)
        elif line.startswith("+SITE/ID"):
            lon,lat = read_stations_latlon(snx,station)
            
    snx.close()
    return [gps,(lon,lat)]


# snx, wrf [if coords are not provided from snx => lat,lon], station id, stat1.dat, stat2.dat, (output file, default is text)
argv = {
    "snx_file": '',
    "wrf_file": '',
    "station": '',
    "output_file": '', #optional
}
#TODO integrate stat1 and stat2 files directly
# cli arguments
if len(sys.argv) == 1:
    print("Usage: python3 gnut_iwv.py --snx_file snx_file --wrf_file wrf_file --station station [--output_file output_file]")
    sys.exit(1)
for i in range(1,len(sys.argv),2):
    if len(sys.argv) < i+1:
        print("Invalid arguments. Exiting...")
        sys.exit(1)
    argv[sys.argv[i][2:]] = sys.argv[i+1]

if argv['snx_file'] == '' or argv['wrf_file'] == '' or argv['station'] == '' or argv['gps_stat_file'] == '' or argv['met_stat_file'] == '':
    print("Missing required arguments. Exiting...")
    sys.exit(1)


try:
    gps_all, (lon,lat) = read_gps_from_snx(argv["snx_file"],argv["station"])
    if len(gps_all) == 0:
        print("No GPS data found. Exiting...")
        sys.exit(1)
    #gps_all[i][0]=station
    #gps_all[i][1]=datetime
    #gps_all[i][2]=ZTD

    if lon == -1 or lat == -1:
        print("No coordinates found. Exiting...")
        sys.exit(1)

    #met
    #TODO why is met in 2 dimensional array (time ?, multiple wrfs ?)
    met_all = [read_met_from_wrf(argv['wrf_file'],argv["station"],lon,lat)]
    if len(met_all[0]) == 0:
        print("No data found from wrf file. Exiting...")
        sys.exit(1)
    # print(met_all)

    #met_all[i][0]=station
    #met_all[i][1]=datetime
    #met_all[i][2]=temp
    #met_all[i][3]=pressure

    #coords
    fid = open(argv['gps_stat_file'])
    gpsstat = fid.readlines()
    fid.close()

    gpsstat[0] = gpsstat[0].removesuffix('\n').split()
    gpsstat[0][0] = int(gpsstat[0][0])
    gpsstat[0][1] = float(gpsstat[0][1])
    gpsstat[0][2] = float(gpsstat[0][2])
    gpsstat[0][3] = int(gpsstat[0][3])
    gpsstat[0][4] = float(gpsstat[0][4])
    gpsstat = gpsstat[0]

    #gpstat[0]=station_id
    #gpstat[1]=station_altitude
    #gpstat[2]=station_latitude
    #gpstat[3]=source_id
    #gpstat[4]=station_longitude

    fid = open(argv['met_stat_file'])
    metstat = fid.readlines()
    fid.close()

    metstat[0] = metstat[0].removesuffix('\n').split('\t')
    metstat[0][0] = int(metstat[0][0])
    metstat[0][1] = float(metstat[0][1])
    metstat[0][2] = float(metstat[0][2])
    metstat[0][3] = int(metstat[0][3])
    metstat = metstat[0]

    #metstat[0]=station_id
    #metstat[1]=station_altitude
    #metstat[2]=station_latitude
    #metstat[3]=source_id

    #average datetime intervals

    t = met_all[0][1]
    step = timedelta(0,0,0,0,5,0,0) # 5 mins
    met = []
    gps = []

    while t <= met_all[-1][1] + step:
        celc = 0
        hpa = 0
        count = 0
        for i in range(len(met_all)):
            # if between step time 
            if met_all[i][1] > t-step/2 and met_all[i][1] < t+step/2:
                celc += met_all[i][2]
                hpa += met_all[i][3]
                count += 1

        # take average
        if count > 0:
            met.append([t,celc/count,hpa/count])
        
        ztd = 0
        count = 0
        for i in range(len(gps_all)):
            # if between step time 
            # print(gps_all[i][1])
            # print(t-step/2)
            if gps_all[i][1] > t-step/2 and gps_all[i][1] < t+step/2:
                ztd += gps_all[i][2]
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
    press = 1013.25 * ( - ( 1 - 0.0000226 * metstat[1] ) ** 5.225 + ( 1 - 0.0000226 * gpsstat[2] ) ** 5.225 );  
    g = -9.806 #%m/s^2
    M = 0.0289644 #%kg/mol
    R = 8.31432 #%N·m/(mol·K)
    T = 288.15 #%K
    L = -0.0065 #%Temperature Lapse Rate K/m

    temp = - L * (metstat[1] - gpsstat[1])
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

        gpsmet[i][3] *= (T/(T+L*(metstat[1]-gpsstat[1])))**(g*M/(R*L))

        ef.append(1-c2*math.cos(2*(gpsstat[2]*math.pi)/180) - c3*gpsstat[1]/1000)

        # same as line 152 ?
        Tm.append(70.2 + 0.72 * (gpsmet[i][2]+273.16))

        ak.append((10.0**5)/(461.51*(((3.776*(10.0**5))/Tm[-1] + 22))))

        gpsmet[i].append((c1*gpsmet[i][3])/ef[-1]) # zhd

        gpsmet[i].append(gpsmet[i][1] - gpsmet[i][-1]) # zwd

        gpsmet[i].append(ak[-1]*gpsmet[i][-1]*1000) # iwv

        # gps station id
        # gpsmet[i].append(gpsstat[0])
        # gps source id
        gpsmet[i].append(gpsstat[3])
        # met source_id
        gpsmet[i].append(metstat[3])
        # station latitude
        gpsmet[i].append(gpsstat[2])
        # station altitude
        gpsmet[i].append(gpsstat[1])
        # station longitude
        gpsmet[i].append(gpsstat[4])

    #gpsmet[i][0] = time
    #gpsmet[i][1] = ztd
    #gpsmet[i][2] = temp
    #gpsmet[i][3] = pressure
    #gpsmet[i][4] = zhd
    #gpsmet[i][5] = zwd
    #gpsmet[i][6] = iwv
    #gpsmet[i][8] = source gnss id
    #gpsmet[i][9] = source met id
    #gpsmet[i][10] = station_latitude
    #gpsmet[i][11] = station_altitude
    #gpsmet[i][12] = station_longitude

    # TODO Find out if need to save in troposinex format
    if argv['output_file'] != '':
        print("Writing to file {0}".format(argv['output_file']))
        fid = open(argv['output_file'],'w')
        fid.write('time,ztd,temp,pressure,zhd,zwd,iwv,source_gnss_id,source_met_id,station_latitude,station_altitude,station_longitude\n')
        for i in range(len(gpsmet)):
            fid.write('{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}\n'.format(gpsmet[i][0],gpsmet[i][1],gpsmet[i][2],gpsmet[i][3],gpsmet[i][4],gpsmet[i][5],gpsmet[i][6],gpsmet[i][7],gpsmet[i][8],gpsmet[i][9],gpsmet[i][10],gpsmet[i][11]))
        fid.close()
    else:
        for i in range(len(gpsmet)):
            print('{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}'.format(gpsmet[i][0],gpsmet[i][1],gpsmet[i][2],gpsmet[i][3],gpsmet[i][6],gpsmet[i][8],gpsmet[i][9],gpsmet[i][10],gpsmet[i][11],gpsmet[i][12]))

    print("Done.")
except FileNotFoundError as e:
    print("File not found: {0}. Exiting...".format(e.filename))
    sys.exit(1)
