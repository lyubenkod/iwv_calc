from netCDF4 import Dataset as netcdf
import numpy as np

def getclosest_ij(lons,lats,latpt,lonpt):
  # find squared distance of every point on grid
  dist_sq = (lats-latpt)**2 + (lons-lonpt)**2
  # 1D index of minimum dist_sq element
  minindex_flattened = dist_sq.argmin()
  # Get 2D index for latvals and lonvals arrays from 1D index
  return np.unravel_index(minindex_flattened, lats.shape)

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
west_east = ncfile.dimensions['west_east']
south_north = ncfile.dimensions['south_north']

# Print the variables
# print(temp[0].size)
# print(pres[0].size)
# print(lon[0].size)
# print(lat[0].size)

# ot snx file tmp\BGR-RT-xxxxx-TEF-FIX-xxxx-IF_240223_1400.snx2
# BGER00BGR  A XXXXXXXXX P Bardarski geran/Bulg/B  23.953740  43.541928   201.781   167.801
i,j = getclosest_ij(lat[0][:],lon[0][:],23.953740,43.541928)
# print(i,j)
print(pres[0][i][j]/100)
print(temp[0][i][j]-273.15)

# Close the NetCDF file
ncfile.close()

