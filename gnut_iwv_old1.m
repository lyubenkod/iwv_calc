function gnut_iwv;

% This matlab script is intended for processing ZTD into IWV
% Started on 22.08.2014
% Finished on 25.08.2014
% Barometric formula added on 11.02.2015
% Modified for SUADA 4 database in November 2015
% Modified for SUADA 5 database in January 2020
% Modified for SUADA 5 database in January 2020

% --------------------------------------------Read SYNOP---------------------------------------------------------- 

   aiai = strcat('/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/met.dat')
   fid=fopen(aiai);
   met_all = fscanf(fid, '%d %4d-%2d-%2d %2d:%2d:%2d %f %f', [9 20000]);
   fclose(fid);

   met_all(10,:) = datenum(met_all(2,:), met_all(3,:), met_all(4,:), met_all(5,:), met_all(6,:), met_all(7,:))

   [s1,s2]= size(met_all)

   for i=1:s2
   if ( met_all(8,i) > 200 )
     met_all(8,i) = met_all(8,i) - 273.15;
   end
   end

   %met_all(1,:)=station 				
   %met_all(2,:)=year					
   %met_all(3,:)=month					
   %met_all(4,:)=day of the month			
   %met_all(5,:)=hour					
   %met_all(6,:)=minute 				
   %met_all(7,:)=second
   %met_all(8,:)=temperature				
   %met_all(9,:)=pressure
   %met_all(10,:)=datenum			

% --------------------------------------------Read GPS_IN--------------------------------------------------------- 

   oioi= strcat('/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/gps.dat')
   fid=fopen(oioi);
   gps_all = fscanf(fid,'%d %4d-%2d-%2d %2d:%2d:%2d %f',[8 50000]);
   fclose(fid);

   gps_all(9,:) = datenum(gps_all(2,:), gps_all(3,:), gps_all(4,:), gps_all(5,:), gps_all(6,:), gps_all(7,:))

   [s3,s4]= size(gps_all)

   %gps_all(1,:)=station     					
   %gps_all(2,:)=year        				
   %gps_all(3,:)=month					
   %gps_all(4,:)=day of the month				
   %gps_all(5,:)=hour	      				
   %gps_all(6,:)=minute 				
   %gps_all(7,:)=second
   %gps_all(8,:)=ZTD					
   %gps_all(9,:)=datenum
								
% --------------------------------------------Read COORDINATE-----------------------------------------------------

   stat1 = strcat('/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/stat1.dat')
   fid=fopen(stat1);
   gpsstat = fscanf(fid, '%d %f %f %d %f', [5 1]);
   fclose(fid);

   %gpsstat(2)=station_altitude
   %gpsstat(3)=station_latitude
   %gpsstat(4)=source_id
   %gpsstat(5)=station_longitude

   stat2 = strcat('/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/stat2.dat')
   fid=fopen(stat2);
   metstat = fscanf(fid, '%d %f %f %d', [4 1]);
   fclose(fid);

   %metstat(1)=station_id
   %metstat(2)=station_altitude
   %metstat(3)=station_latitude
   %metstat(4)=source_id

%% --------------------------------------------Average Datetime intrvals-------------------------------------------
%  
%  startt=met_all(11,1); %this is because SYNOP data come in rounded hours, while GPS may come in different from rounded datasets
%  endt=met_all(11,s2);
%
%
%t=startt;
%step = datenum(0, 0, 0, 0, 15, 0);
%mm = 1;
%gg = 1;
%while (t <= endt + step)
%
%  celc = 0;
%  hpa = 0;
%  mn = 0;
%  for m=1:s2
%    if ( met_all(11,m) > t-step/2 && met_all(11,m) < t+step/2 )
%      celc = celc + met_all(8,m);
%      hpa = hpa + met_all(9,m);
%      mn = mn + 1;
%    end
%  end
%  if ( mn > 0 )
%    met(1,mm) = t;
%    met(2,mm) = celc/mn;
%    met(3,mm) = hpa/mn;
%    mm = mm + 1;
%  end
%
%  ztd=0;
%  gn = 0;
%  for g=1:s4
%    if ( gps_all(12,g) > t-step/2 && gps_all(12,g) < t+step/2 )
%      ztd = ztd + gps_all(8,g);
%      gn = gn + 1;
%    end
%  end
%  if ( gn > 0 )
%    gps(1,gg) = t;
%    gps(2,gg) = ztd/gn;
%    gg = gg + 1;
%  end
%
%  t = t + step;
%
%end
%
%display (gps)
%display (met)
%
%   [s5,s6]= size(gps)
%   [s7,s8]= size(met)
%
% --------------------------------------------Datetime matching---------------------------------------------------

   gpsmet=[];
   for l=1:s4
     for ll=1:s2
      if (gps_all(6,l) == met_all(6,ll))   
      gps_met=[gps_all(9,l); gps_all(8,l);  met_all(8,ll); met(9,ll); ];
      %gps_met_suada_4 (time, ztd, temp, press)
      gpsmet=[gpsmet gps_met];
      end   
      end
   end  

   [s9,s10] = size(gpsmet)
    display (gpsmet);
% --------------------------------------------IWV calculations----------------------------------------------------

   press = 1013.25 * ( - ( 1 - 0.0000226 * metstat(2) ) ^ 5.225 + ( 1 - 0.0000226 * gpsstat(2) ) ^ 5.225 );  

g=-9.806;%m/s^2
M=0.0289644;%kg/mol
R=8.31432;%N·m/(mol·K)
T=288.15;%K
L=-0.0065;%Temperature Lapse Rate K/m

   temp = -L * ( metstat(2) - gpsstat(2));

c0=0.0000024;
c1=0.0022768;
c2=0.00266;
c3=0.00028;

   for m=1:s10
     gpsmet(3,m)=gpsmet(3,m)+temp;
     T=gpsmet(3,m)+273.15;
     gpsmet(4,m)=gpsmet(4,m)*(T/(T+L*(metstat(2) - gpsstat(2))))^(g*M/(R*L));
     ef(m)=1-c2*cos(2*(gpsstat(3)*pi)/180)-c3*gpsstat(2)/1000;  
     Tm(m) = 70.2 + 0.72 * (gpsmet(3,m)+273.16);
     ak(m) = (10.^5)/( 461.51*( ((3.776*10.^5)/Tm(m) + 22 ) ) );

     gpsmet(5,m)=(c1*gpsmet(4,m))/ef(m); % zhd
	  lh1(m)=((c1+c0)*gpsmet(4,m))/ef(m);
	  lh2(m)=((c1-c0)*gpsmet(4,m))/ef(m);
     gpsmet(6,m) = gpsmet(2,m) - gpsmet(5,m); % zwd
     gpsmet(7,m)=ak(m)*gpsmet(6,m)*1000; % iwv
%     if ( gpsmet(8,m) >= 0)
%     gpsmet(12,m)=gpsmet(8,m)/gpsmet(11,m)*100 %pe by bordi
%     end
     gpsmet(8,m)=gpsstat(1);
     gpsmet(9,m)=gpsstat(4);
     gpsmet(10,m)=metstat(4);
     gpsmet(11,m)=gpsstat(3);
     gpsmet(12,m)=gpsstat(2);
     gpsmet(13,m)=gpsstat(5);
%     H=2.11;
%     a=1.02;
%     gpsmet(16,m)=a*gpsmet(11,m)*exp(((gpsstat(2)/1000)-0.5 )/H);
   end


    display (gpsmet);
%------------------------------------------------------------------------------------------------


   %gpsmet(1,:)=time 
   %gpsmet(2,:)=ztd
   %gpsmet(3,:)=temperature 					
   %gpsmet(4,:)=pressure
   %gpsmet(5,:)=zhd
   %gpsmet(6,:)=zwd
   %gpsmet(7,:)=iwv
   %gpsmet(8,:)=station id
   %gpsmet(9,:)=source gnss id
   %gpsmet(10,:)=source met id
  

   ready= strcat('/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP/tmp/ready.dat')
   fid=fopen(ready,'w');
   for i=1:s10
     if gpsmet(7,i) > 0 
    fprintf(fid,'%s %f %1.4f %f %f %f %f %f %f %f %f %f \n ', datestr(datevec(round(gpsmet(1,i)*1440)/1440), 31), gpsmet(1,i), gpsmet(2,i), gpsmet(3,i), gpsmet(4,i), gpsmet(7,i), gpsmet(8,i), gpsmet(9,i), gpsmet(10,i), gpsmet(11,i),gpsmet(12,i),gpsmet(13,i));
%   fprintf(fid,'%s %f %1.4f %f %f %f %f %f %f %f %f %f %f %f \n ', datestr(datevec(round(gpsmet(1,i)*1440)/1440), 31), gpsmet(1,i), gpsmet(2,i), gpsmet(3,i), gpsmet(4,i), gpsmet(7,i), gpsmet(8,i), gpsmet(9,i), gpsmet(10,i), gpsmet(11,i), gpsmet(12,i), gpsmet(13,i));
%   fprintf(fid,'%s %f %1.4f %f %f %f %f %f  %f \n ', datestr(datevec(round(gpsmet(1,i)*1440)/1440), 31), gpsmet(1,i), gpsmet(2,i), gpsmet(3,i), gpsmet(4,i), gpsmet(7,i), gpsmet(8,i), gpsmet(9,i), gpsmet(10,i));
   %The datevec rounding is made in order to clear the last second shift during the processing. It is a problem with the precision of the datenum function, which can not always precisely distinguish round hours.
     end
   end
   fclose(fid);

   clear all;
 
