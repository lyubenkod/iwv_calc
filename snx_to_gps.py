from math import floor
from datetime import datetime, timedelta

snx = open("tmp/BGR-RT-xxxxx-TEF-FIX-xxxx-IF_240223_1300.snx2",'r')
started_reading = False
for line in snx:
    if line.startswith("+TROP/SOLUTION"):
        started_reading = True
    elif started_reading:
        if line.startswith(" SUZF00BGR"):
            formatted = line.strip().split(' ')[:3]
            # formatted[0] = 3467
            # Reading TROTOT
            date = formatted[1].split(':')
            day_in_seconds = float(date[2])

            day_in_hours = day_in_seconds/3600
            hours = floor(day_in_hours)
            minutes_full = (day_in_hours-hours)*60
            minutes = round(minutes_full,3)
            seconds = round((minutes_full-minutes)*60,3)
            actual_date = datetime(int(date[0]),1,1) + timedelta(int(date[1])-1)
            actual_date += timedelta(0,seconds,0,0,minutes,hours,0)
            formatted[1] = actual_date.strftime("%Y-%m-%d %H:%M:%S")
            
            formatted[2] = round(float(formatted[2])/1000,4)
            print(formatted)
        elif line.startswith("-TROP/SOLUTION"):
            started_reading = False

        
snx.close()