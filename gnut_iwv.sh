#!/bin/bash

# This program processes raw GNSS data & WRF data into IWV
# Started on 14.01.2014
# Finished on 18.01.2014
# Debugged on 19.01.2014
# In service since 20.01.2014
# Modified with barotropic formula on 11.02.2015
# Modified for SUADA v4 on 20.11.2015
# Modified for SUADA v5 on 01.12.2018
# Modified for GNUT on 16.07.2021

#Load modules since script is executed from non-interactive session (crontab)
. /opt/Modules/modules.sh
module load matlab

DBHOST="fs002"
DBUSER="meteo"
DBPASSWD="m3t30d4t4"
DBNAME="suada_5"

mkdir -p /work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP
metfile=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/met.dat
gpsfile=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/gps.dat
statfile1=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/stat1.dat
statfile2=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/stat2.dat
datafile=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/ready.dat
datafile2=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/complete.dat
datafile3=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/tro.dat
#+----+---------------------+
#| 23 | GNUT PPP            |
#+----+---------------------+
#Write GNSS source ID:"
sg=23

#echo "
#+----+-----------------------+
#| ID | Name                  |
#+----+-----------------------+
#| 73 | WRF_3_7_1             |
#+----+-----------------------+
#Write SYNOP source ID:"
sm=73

YYYY=$(date -u --date='1 hour ago' +"%Y")
YY=$(date -u --date='1 hour ago'  +"%y")
MM=$(date -u --date='1 hour ago' +"%m")
DD=$(date -u --date='1 hour ago'  +"%d")
DOY=$(date -u --date='1 hour ago'  +"%j")

UTC=$(date -u --date='1 hour ago'  | awk '{print $4}' | cut -d":" -f 1)

#echo "Write start of processing period in format YYYY MM DD:"
#read syyyy ssmm ssdd
syyyy=$YYYY
ssmm=$MM
ssdd=$DD

#echo "Write end of processing period in format YYYY MM DD:"
#read eyyyy eemm eedd
eyyyy=$YYYY
eemm=$MM
eedd=$DD

datafile4=/work/mg/pl/wrf/scripts/bulgaria/GNSS_GNUT/GNUT_GNS_IWV_${YYYY}${DOY}${UTC}00_00U_00U.TRO
# These cycles are done in order to avoid overflowing of the buffer of MySQL. The idea is to process only a month at a time without the user knowing that there is such a cyclical processing
SS="31 50 51 52 53 54 55 56 57 59 60 61"
#SS="31 50 51 52 53 54 55 56 57"
#SS="50 51 52 53 55 56 57"
for i in $SS # StationID cycle
#for i in {50..61} # StationID cycle
 do
   st=$i 

 smm=$ssmm

while [ $smm -le $eemm ] #Month cycle
  do
    emm=$smm

# From the previous comment untill this line we are ensuring the selection of data for only one month number at a time with cycling between the chosen months

  if [ $ssmm -eq $eemm ]
  then
    smm=$ssmm
    emm=$eemm
    sdd=$ssdd
    edd=$eedd
  else
    if [ $smm -eq $ssmm ]
    then
      sdd=$ssdd
      edd=31
    else
      if [ $smm -eq $eemm ]
      then
        sdd=1
        edd=$eedd
      else
        sdd=1
        edd=31
      fi
    fi
  fi


# From the previous comment untill this line we are ensuring the selection of data for all the chosen days within only one month number with cycling between all the chosen days

echo "StationID=$st Source_GNSS_ID=$sg Source_SYNOP_ID=$sm Start_Date=$syyyy $smm $sdd End_Date=$eyyyy $emm $edd"


ssg=`/usr/bin/mysql -u $DBUSER -p$DBPASSWD -N -h $DBHOST $DBNAME --execute "
SELECT ID
FROM SENSOR
WHERE StationID=$st AND SourceID=$sg"`

ssm=`/usr/bin/mysql -u $DBUSER -p$DBPASSWD -N -h $DBHOST $DBNAME --execute "
SELECT ID
FROM SENSOR
WHERE StationID=$st AND SourceID=$sm"`

echo "stat=$st SSG=$ssg SSM=$ssm Start_Date=$syyyy $smm $sdd End_Date=$eyyyy $emm $edd"



# read station coordinated  from SUADA--------------------------------------------------------------

/usr/bin/mysql -u $DBUSER -p$DBPASSWD -N -h $DBHOST $DBNAME --execute "
SELECT COORDINATE.StationID, COORDINATE.Altitude, COORDINATE.Latitude, SENSOR.SourceID, COORDINATE.Longitude FROM COORDINATE, SENSOR WHERE COORDINATE.StationID = SENSOR.StationID AND SENSOR.StationID = ' $st ' AND SENSOR.SourceID = ' $sg ' AND COORDINATE.InstrumentID = 1;" > $statfile1

/usr/bin/mysql -u $DBUSER -p$DBPASSWD -N -h $DBHOST $DBNAME --execute "
SELECT MAX(SENSOR.StationID), AVG(NWP_IN_1D.Altitude), AVG(NWP_IN_1D.Latitude), MAX(SENSOR.SourceID) FROM NWP_IN_1D, SENSOR WHERE NWP_IN_1D.SensorID = SENSOR.ID AND SENSOR.ID = ' $ssm ' AND NWP_IN_1D.Datetime between '$syyyy-$smm-$sdd $UTC:00:00' AND '$eyyyy-$emm-$edd $UTC:59:59';" > $statfile2

# READ Ps and Ts from WRF 1D model table------------------------------------------------------------

/usr/bin/mysql -u $DBUSER -p$DBPASSWD -N -h $DBHOST $DBNAME --execute "
SELECT SensorID, Datetime, Temperature, Pressure
FROM NWP_IN_1D
WHERE SensorID = ' $ssm ' AND Datetime between '$syyyy-$smm-$sdd $UTC:00:00' AND '$eyyyy-$emm-$edd $UTC:59:59';" > $metfile

# READ ZTD from GNSS_IN table------------------------------------------------------------------------
/usr/bin/mysql -u $DBUSER -p$DBPASSWD -N -h $DBHOST $DBNAME --execute "
SELECT SensorID, Datetime, ZTD 
FROM GNSS_IN
WHERE SensorID = ' $ssg ' AND Datetime between '$syyyy-$smm-$sdd $UTC:00:00' and '$eyyyy-$emm-$edd $UTC:59:59';" > $gpsfile

if [ -s "$metfile" ]
then

if [ -s "$gpsfile" ]
then

sed -i s/NULL/NaN/g $metfile 
sed -i s/NULL/NaN/g $gpsfile 

matlab -nodisplay  -nojvm -nodesktop < gnut_iwv.m > /work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/matlab_iwv.log 2> err_23_73_iwv.log

echo "
+----------------------------+
| MATLAB processing complete |
+----------------------------+"

$rm  $datafile2  
 echo "Start import file: " $datafile
  awk -f gnut_iwv.awk  $datafile  >>  $datafile2  
  awk -f gnut_iwv_ftp.awk  $datafile  >  $datafile3  
  sed -f gnut_iwv_ftp.sed  $datafile3  >> $datafile4
 echo "End import"

sed -i s/NaN/NULL/g $datafile2 
sed -i s/NaN/NULL/g $datafile4 

#echo "
#+---------------------------------------------------------------+
#|                                                               |
#| !!! Please wait untill data is imported into the database !!! |
#|                                                               |
#+---------------------------------------------------------------+"


/usr/bin/mysql --local-infile -u\'$DBUSER\' -p$DBPASSWD -h $DBHOST $DBNAME << EOF
LOAD DATA LOCAL INFILE '/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/complete.dat' REPLACE INTO TABLE GNSS_OUT (StationID,SourceGpsID,SourceMetID,Datetime,Temperature,Pressure,ZTD,IWV);
DELETE FROM GNSS_OUT WHERE Datetime='0000-00-00 00:00:00';
EOF

echo "
+---------------------------------------------------------------------------------+
| Processing complete for StationID=$st Source_GNSS_ID=$sg Source_SYNOP_ID=$sm    |
| Start_Date=$syyyy $smm $sdd End_Date=$eyyyy $emm $edd                           |
| Please chack if the data is successfully uploaded into the database if possible |
| Thank you!                                                                      |
+---------------------------------------------------------------------------------+"


else 
  echo "
+-----------------------------------------------------------------------+
|                                                                       |
| !!! No GPS data for this period and source for station number $st !!! |
|                                                                       |
+-----------------------------------------------------------------------+
"
fi

else 
  echo "
+-------------------------------------------------------------------------+
|                                                                         |
| !!! No SYNOP data for this period and source for station number $st !!! |
|                                                                         |
+-------------------------------------------------------------------------+
"
fi

  smm=${smm#0}
  smm=$(( $smm + 1 ))
  done #end of while cycle
 done #this done ends the cycling of the station numbers
 cp $datafile4 /work/mg/suada5/Bernese52/HSA/rinex/BINCA/RT
 cp $datafile4 /work/mg/suada5/Bernese52/HSA/rinex/BINCA/GNSS/SUG1_GNS_IWV_${YYYY}${DOY}${UTC}00_00U_00U.TRO

echo "
+---------------------------------------------------------------------------------+
| Please chack if the data is successfully uploaded into the database if possible |
| Thank you!                                                                      |
+---------------------------------------------------------------------------------+"
#rm -f $dbfile
