from datetime import datetime,timedelta
import math

def read_gps_from_snx(file,stations):
    snx = open(file,'r')
    result = []
    started_reading = False
    for line in snx:
        if line.startswith("+TROP/SOLUTION"):
            started_reading = True
        elif started_reading:
            for station in stations:
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
        elif line.startswith("-TROP/SOLUTION"):
            started_reading = False
    snx.close()
    return result

#met
fid = open('tmp/met.dat')
met_all = fid.readlines()
fid.close()

# cleanup and datetime conversion
for i in range(len(met_all)):
    met_all[i] = met_all[i].removesuffix('\n').split('\t')
    met_all[i][1] = datetime.strptime(met_all[i][1],'%Y-%m-%d %H:%M:%S')
    met_all[i][2] = float(met_all[i][2])
    met_all[i][3] = float(met_all[i][3])

# No kelvin
for i in range(len(met_all)):
    if met_all[i][2] > 200:
        met_all[i][2] -= 273.15

#met_all[i][0]=station
#met_all[i][1]=datetime
#met_all[i][2]=temp
#met_all[i][3]=pressure

#gps
# fid = open('tmp/gps.dat')
# gps_all = fid.readlines()
# fid.close()
gps_all = read_gps_from_snx('tmp/BGR-RT-xxxxx-TEF-FIX-xxxx-IF_240223_1400.snx2',["SUZF00BGR"])

# cleanup and datetime conversion
# for i in range(len(gps_all)):
#     gps_all[i] = gps_all[i].removesuffix('\n').split('\t')
#     gps_all[i][1] = datetime.strptime(gps_all[i][1],'%Y-%m-%d %H:%M:%S')
#     gps_all[i][2] = float(gps_all[i][2])

#gps_all[i][0]=station
#gps_all[i][1]=datetime
#gps_all[i][2]=ZTD


#coords
fid = open('tmp/stat1.dat')
gpsstat = fid.readlines()
fid.close()

gpsstat[0] = gpsstat[0].removesuffix('\n').split('\t')
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

fid = open('tmp/stat2.dat')
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
    gpsmet[i].append(gpsstat[0])
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
#gpsmet[i][7] = station id
#gpsmet[i][8] = source gnss id
#gpsmet[i][9] = source met id
#gpsmet[i][10] = station_latitude
#gpsmet[i][11] = station_altitude
#gpsmet[i][12] = station_longitude

for i in range(len(gpsmet)):
    print(f'{gpsmet[i][0]} {gpsmet[i][1]} {gpsmet[i][2]} {gpsmet[i][3]} {gpsmet[i][6]} {gpsmet[i][7]} {gpsmet[i][8]} {gpsmet[i][9]} {gpsmet[i][10]} {gpsmet[i][11]} {gpsmet[i][12]}')