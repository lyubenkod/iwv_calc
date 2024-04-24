import sys
from netCDF4 import Dataset as netcdf
from datetime import datetime,timedelta

import numpy as np
def process_station_tro(station, ncfile):
    result = True
    try:
        x0 = station['long']
        y0 = station['latt']
        z0 = station['alt']
        i0 = station['i0']
        j0 = station['j0']

        # 1D FIELDS:
        # T2, [K]: temperature on 2m height:
        T2 = ncfile.variables['T2'][0]
        # Q2, [kg/kg] - specific humidity (will be inserted in tropo txt format):
        Q2 = ncfile.variables['Q2'][0]
        # Pressure, [Pa]:
        Pressure = ncfile.variables['PSFC'][0]
        # PBLH, [m] - planatary boundary layer height:
        PBLH = ncfile.variables['PBLH'][0]
        # HGT, [m] - 1D height above sea level
        HGT = ncfile.variables['HGT'][0]
        # The following 4 fields are in [mm]:
        RAINNC = ncfile.variables['RAINNC'][0]
        SNOWNC = ncfile.variables['SNOWNC'][0]
        GRAUPELNC = ncfile.variables['GRAUPELNC'][0]
        HAILNC = ncfile.variables['HAILNC'][0]
        # Precipitation, [mm]:
        Precipitation = RAINNC + SNOWNC + GRAUPELNC + HAILNC
        
        # 3D FIELDS:
        # T, [K] - temperature:
        T = ncfile.variables['T'][0]
        # P, [Pa] - perturbation pressure:
        P = ncfile.variables['P'][0]
        # PB, [Pa] - base state pressure
        PB = ncfile.variables['PB'][0]
        # PHB, [m] - base state geopotential height:
        PHB = ncfile.variables['PHB'][0]
        # PH, [m] - perturbation geopotential height:
        PH = ncfile.variables['PH'][0]
        # QVAPOR, [kg/kg] - water vapour mixing ratio:
        QVAPOR = ncfile.variables['QVAPOR'][0]

        # Import 1D fields
        # press, [hPa]:
        press = Pressure[i0][j0]/100.
        # height, [m]:
        heigth = HGT[i0][j0]
        # Q2_humi, [g/kg]:
        Q2_humi = Q2[i0][j0]*1000.
        # Calculation of zhd, [m] - zenith hydrostatic delay
        zhd = (0.0022768*(float(press)))/(1.-0.00266*np.cos(2*(float(z0))*(3.1416/180.))-(0.00028*(float(heigth))/1000.))
        
        # pblh, [m] - planatary boundary layer height:
        pblh = PBLH[i0][j0]
        # temp, [C]:
        temp = T2[i0][j0]-273.15
        # rain, [mm]:
        rain = Precipitation[i0][j0]
    
        #print('Inserting into TROPOSINEX txt format. Name: {0} [{1}, {2}, {3}] -> [Temperarture [C]: {4}, Pressure [hPa]: {5}, Rain [mm]: {6}, PBL HEIGHT [m]: {7}, Zenit Heigth Delay [x]: {8}, Q2 [kg/kg]: {9}] '
        #    .format(station['name'],
        #        x0,
        #        y0,
        #        z0,
        #        temp,
        #        press,
        #        rain,
        #        pblh,
        #        zhd,
        #        Q2_humi))

        # 3D data insertion:
        bottom_top = len(T)
        # First, calculation of tk:
        # Rd, Cp, Rd_Cp are used for 3D calculation of
        # tk (absolute temperature [K], and then
        # it's converted to [C]):
        Rd  = 287.0
        Cp  = 7.0 * Rd / 2.0
        Rd_Cp  = Rd / Cp # dimensionless
        Rv = 461.51
        # The following Tm and k1 are used for calculation of ZWD, ZTD later:
        # Tm, [K] - weighted temperature mean:
        Tm = 70.2 + 0.72 * T2[i0][j0]
        k1 = (10**6) / ( Rv*(((3.766 * 10**5)/Tm) + 22.) )

        IWV = 0.
        # # Calculate date variables
        # date_YYYY = date.timetuple().tm_year
        # date_DOY = date.timetuple().tm_yday
        # date_SSSSS = date.timetuple().tm_hour * 60 * 60
        # date_HH = date.timetuple().tm_hour
        # date_MM = date.timetuple().tm_min
        # # Convert to strings:
        # YYYY_st = str(date_YYYY)
        # DOY_st = '{:03d}'.format(date_DOY)
        # SSSSS_st = '{:05d}'.format(date_SSSSS) #str(date_SSSSS)
        # HH_st = '{:02d}'.format(date_HH) #str(date_HH)
        # MM_st = '{:02d}'.format(date_MM) #str(date_MM)

        for k in range(0, bottom_top):
            if k <= 41:
                # Compute specific humidity q1 and q2 from mixing ratio QVAPOR*1000. in [g/kg]:
                q1 =  (QVAPOR[k][i0][j0] * 1000.) / ( (QVAPOR[k][i0][j0] * 1000.) + 1. )
                q2 =  (QVAPOR[k+1][i0][j0] * 1000.) / ( (QVAPOR[k+1][i0][j0] * 1000.) + 1. )

                # Compute water vapour partial pressure with model pressure = (P+PB)/100. in [hPa]:
                # PP = (P[k][i0][j0]+PB[k][i0][j0])
                e_k   = ( ((P[k][i0][j0]+PB[k][i0][j0]) / 100.)   * q1 ) / ( 0.622 + ( 0.378 * q1 ))
                e_kp1 = ( ((P[k+1][i0][j0]+PB[k+1][i0][j0]) / 100.) * q2 ) / ( 0.622 + ( 0.378 * q2 ))

                # Compute water vapour density with T [K]
                # T is perturbation potential temerature TT=T+300. Total Potential temperature [K]
                # Model level temrature is computed TT = T * ( ((P+PB)/100000.) ^ (2/7)) [K]
                # TT = (T[k][i0][j0] + 300.) * (( (P[k][i0][j0]+PB[k][i0][j0])/100000. )**(2./7.))
                # NB to compute the temerature from potential temprature pressure is in [Pa]

                ro_k   = e_k   / ( Rv * ( (T[k][i0][j0] + 300.) * ( ((P[k][i0][j0]+PB[k][i0][j0])/100000.)**(2./7.) ) ) )
                ro_kp1 = e_kp1 / ( Rv * ( (T[k+1][i0][j0] + 300.) * ( ((P[k+1][i0][j0]+PB[k+1][i0][j0])/100000.)**(2./7.) ) ) )

                TT = (T[k][i0][j0] + 300.) * (( (P[k][i0][j0]+PB[k][i0][j0])/100000. )**(2./7.))
                PP = (P[k][i0][j0]+PB[k][i0][j0])/100.
                # Model level height is computed using geopotenial H=(PH + PHB)/9.81
                h_k = (PH[k][i0][j0]+PHB[k][i0][j0])/9.81
                h_kp1 = (PH[k+1][i0][j0]+PHB[k+1][i0][j0])/9.81
                delta_height = abs(h_kp1 - h_k)

                # Integrated Water Vapour [kg/m^2]:
                IWV = IWV + ( ((ro_k+ro_kp1) / 2.)  * delta_height )

        # Compute Zenith Wet Delay (ZWD, [m]) and Zenith Total Delay (ZTD, [m]):
        ZWD = IWV/(k1*100.) # Divided by 100 to convert from [cm] to [m].
        ZTD = zhd + ZWD

        # In the TROPOSINEX format, zhd, ZTD, ZWD are in [mm]. Therefore, *1000. :
        zhd_mm = zhd*1000.
        ZWD_mm = ZWD*1000.
        ZTD_mm = ZTD*1000.

        # Create result as a dictonary:
        result = {
            'station_name' : station['name'],
            'long'         : station['long'],
            'latt'         : station['latt'],
            'alt'          : station['alt'],
            'IWV'          : IWV,
            'press'        : press,
            'Q2_humi'      : Q2_humi,
            'temp'         : temp,
            'Tm'           : Tm,
            'zhd_mm'       : zhd_mm,
            'ZTD_mm'       : ZTD_mm,
            'ZWD_mm'       : ZWD_mm,
            'q1'           : q1,
            'q2'           : q2
            }

    except Exception as e:
        sys.stderr.write('Error occured in process_station_tro: {error}'.format(error = repr(e)))
    finally:
        return result

ncfile = netcdf('tmp/wrfout_d03_2024-03-14_14_00_00')

station = {
    'name' : 'SUZF00BGR',
    'long' : 23.329108,
    'latt' : 42.673810,
    'alt'  : 639.679,
    'i0'   : 116,
    'j0'   : 66
}
print(process_station_tro(station,ncfile))