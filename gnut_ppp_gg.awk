# This AWK file is written to turn the ANETZ data sent in the new VQAA44 format into a format which can be read into the MySQL database.
# June Morland, November 2006
# Script is modified latter on to prepare input file for GPS table
# Stoyan Pisov, March 2012

BEGIN {OFS="\t"}

#process lines begining with numbers only
$1 ~/^[0-9]/ {

	stationid=$1
	year_2=substr($2,1,4)
	day_year=substr($2,6,3)
	second_min=substr($2,10,5)
	total_ztd=$3
	sigma_ztd=$4

  day_year=int(day_year)
  m = second_min/60
  h = m/60
  hour = int(h) 
 # minute = int(m-hour*60)
  minute = (m-hour*60)
  second = 0
  sigma_u = sigma_ztd/1000
  total_u = total_ztd/1000 

#  if (minute == 59)
#{hour=hour+1;minute=0}

#  if (minute =! 00)
#{minute=0}

 if (year_2>90)
{year=year_2}
 else 
{year=year_2}


 if (year == 1996 || year == 2000 || year == 2004 || year == 2008 || year == 2012 || year == 2016 || year == 2020 )
  {k=1}
  else 
  {k=0} 

 if ( day_year >= 1 ) { if ( day_year <= 31 ) {day=day_year; month=01
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 32 ) { if ( day_year <= 59 + k ) {day=day_year-31; month=02
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 60+k ) { if ( day_year <= 90 + k ) {day=day_year-59+k; month=03
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 91+k ) { if ( day_year <= 121 + k ) {day=day_year-90+k; month=04
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 121+k ) { if ( day_year <= 151 + k ) {day=day_year-120+k; month=05
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 152+k ) { if ( day_year <= 182 + k ) {day=day_year-151+k; month=06
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 182+k ) { if ( day_year <= 212 + k ) {day=day_year-181+k; month=07
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 213+k ) { if ( day_year <= 243 + k ) {day=day_year-212+k; month=08
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 244+k ) { if ( day_year <= 273 + k ) {day=day_year-243+k; month=09
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 274+k ) { if ( day_year <= 304 + k ) {day=day_year-273+k; month=10
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 305+k ) { if ( day_year <= 334 + k ) {day=day_year-304+k; month=11
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }

 if ( day_year >= 335+k ) { if ( day_year <= 365 + k ) {day=day_year-334+k; month=12
  print stationid,year"-"month"-"day" "hour":"minute":"second, sigma_u, total_u} }



         }

