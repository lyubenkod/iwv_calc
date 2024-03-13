# This AWK file preparin data to be uploaded into MODEL_PROCESSED
# June Morland, November 2006
# Script is modified latter on to prepare input file for GNSS_OUT table
# Stoyan Pisov, March 2012
# Script modified to handle null data for SUADA v5
# Tzvetan Simeonov, June 2019

BEGIN {OFS="\t"}

#process lines begining with numbers only
$1 ~/^[0-9]/ {

	station_id=$8
	date=$1
	time=$2
	lat=$11
	lon=$13
	alt=$12
	iwv=$7
	temp=$5
	press=$6
	ztd=$4

#   print station_id, source_met, source_gps, date" "time, lat, alt, iwv, temp, press, ztd
   print station_id, source_met, source_gps, date" "time, lon, lat, alt, iwv, temp, press, ztd

         }

