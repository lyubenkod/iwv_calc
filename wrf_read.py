from netCDF4 import Dataset as netcdf

# Open the NetCDF file
ncfile = netcdf('tmp/wrfout_d03_2024-03-14_14_00_00')

# Extract the variables
time = ncfile.variables['Times']
temp = ncfile.variables['T2']
pres = ncfile.variables['PSFC']
lat = ncfile.variables['XLAT']
lon = ncfile.variables['XLONG']

truelat1 = ncfile.TRUELAT1
truelat2 = ncfile.TRUELAT2
ref_lat  = ncfile.CEN_LAT
ref_lon  = ncfile.CEN_LON
stand_lon= ncfile.STAND_LON
dx = ncfile.DX
dy = ncfile.DY
west_east = ncfile.dimensions['west_east'].size
south_north = ncfile.dimensions['south_north'].size

# Print the variables
press = ncfile.variables['T2']
print(press.size)
#print(press[168][90])

# Close the NetCDF file
ncfile.close()

