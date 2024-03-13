#!/bin/bash -x

# This program downloads and loads into GNUT PPP ZTD in GNSS_IN SUADA table
# Stoyan Pisov, March 2012
# Tzvetan Simeonov, August 2014
# Tzvetan Simeonov, August 2015 for SUADA v4
# Tzvetan Simeonov, April 2019 for SUADAv5
# Guergana Guerova, January 2020 for SUADAv5 BeRTISS
# Guergana Guerova, July 2021 for SUADAv5 GNUT
# Guergana Guerova, September 2023 new GNUT files with 5 min resolution

DBHOST="fs002"
DBUSER="meteo"
DBPASSWD="m3t30d4t4"
DBNAME="suada_5"

YYYY=$(date -u --date='1 hour ago' +"%Y")
YY=$(date -u --date='1 hour ago' +"%y")
MM=$(date -u --date='1 hour ago' +"%m")
DD=$(date -u --date='1 hour ago' +"%d")
UTC=$(date -u --date='1 hour ago' | awk '{print $4}' | cut -d":" -f 1)

#YYYY=$(date -u  +"%Y")
#YY=$(date -u  +"%y")
#MM=$(date -u  +"%m")
#DD=$(date -u  +"%d")
#UTC=$(date -u | awk '{print $4}' | cut -d":" -f 1)

datadir=/work/mg/suada5/Bernese52/HSA/rinex/RT-TROPO/ # where the data is
procdir=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp # this file contains data for mysql database
dbfile=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/gps.dbs # this file contains data for mysql database
processedfile=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/gpsdata.dbs   # where the processed files are kept

     if [ -r "$dbfile" ]
       then
       rm -f $dbfile # remove the database file if it exists already as adding data to it
     fi

     if [ -r "$processedfile" ]
       then
       rm -f $processedfile
     fi
#BGR-RT-CNS91-TEF-FIX-Gxxx-IF_210715_1500.snx2.gz
#BGR-RT-xxxxx-TEF-FIX-xxxx-IF_230901_0800.snx2.gz

#     if [ -s $datadir/"BGR-RT-CNS91-TEF-FIX-Gxxx-IF_"$YY$MM$DD"_"$UTC"00.snx2.gz" ]
     if [ -s $datadir/"BGR-RT-xxxxx-TEF-FIX-xxxx-IF_"$YY$MM$DD"_"$UTC"00.snx2.gz" ]
       then
        cp $datadir/"BGR-RT-xxxxx-TEF-FIX-xxxx-IF_"$YY$MM$DD"_"$UTC"00.snx2.gz" $procdir/"BGR-RT-xxxxx-TEF-FIX-xxxx-IF_"$YY$MM$DD"_"$UTC"00.snx2.gz"   
        gzip -d $procdir/"BGR-RT-xxxxx-TEF-FIX-xxxx-IF_"$YY$MM$DD"_"$UTC"00.snx2.gz"

        echo "Start file: $procdir/"BGR-RT-xxxxx-TEF-FIX-xxxx-IF_"$YY$MM$DD"_"$UTC"00.snx2.gz" "
        sed -f gnut_ppp_gg.sed  $procdir/"BGR-RT-xxxxx-TEF-FIX-xxxx-IF_"$YY$MM$DD"_"$UTC"00.snx2" >> $processedfile  
     
#        # use awk to produce correct format and check for null values

        echo "Start DB inmport file: " $processedfile
        awk -f gnut_ppp_gg.awk  $processedfile  >> $dbfile  

/usr/bin/mysql --local-infile -u\'$DBUSER\' -p$DBPASSWD -h $DBHOST $DBNAME << EOF
LOAD DATA LOCAL INFILE '/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/gps.dbs' REPLACE INTO TABLE GNSS_IN (SensorID,Datetime,Sigma_ZTD,ZTD);
DELETE FROM GNSS_IN WHERE Datetime='0000-00-00 00:00:00';
EOF
  echo "End import"


     fi

#rm -f $dbfile
