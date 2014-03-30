def solar_top (nyear, mon, julian_day, lat, long, utc_lapse, units):
	# Return hourly top of atmosphere solar radiation values for given day.
	# Keys of returned dictionary are hours (LST; no DST adjustment)
	# nyear:		year of model run
	# mon:			month of model run
	# julian_day:	julian day
	# lat:			latitude of station
	# long:			longitude of station
	# utc_lapse:	UTC offset (5 for EST)
	# units:		output units (1=langleys; 2=MJ/m2; 3=W/m2; 4=BTU/ft2)

	import math
	cosZ = {}
	sun_top = {}
	for i in range(24):
		sun_top[i] = 0.0

	# ********* THESE EQUATION INVOLVE DETERMINING THE SOLAR ANGLE *******
	# **    See Walraven 1978:  Calculating the position of the sun Sol. Energy, 20, 193

	intyr = int(4.0*(int((float(nyear))/4.0)))
	lp = 0
	if intyr==nyear: lp = 1

	if mon<=2:
		doy = julian_day - lp
	else:
		doy = julian_day

	delta = float(nyear) - 1980.0
	leap = int(delta/4.0)

	# ********* THIS OUTER LOOP INCREMENTS THE TIME BY SIX MINUTES *******
	# ********* AND THEN DOES RADIATION CALCULATIONS *********

	for hr in range(230):
		ahr = (float(hr)/10.)

		if math.floor(ahr)==ahr:
			ohour = int(math.floor(ahr))
		else:
			ohour = int(math.floor(ahr))+1

		time = delta*365.0 + leap + doy - 1.0 + (ahr/24.0)
		if delta==(leap*4.0): time=time-1.0
		if (delta<0 and delta!=(leap*4.0)): time=time-1.0

		theta = 2.0*math.pi*time / 365.25
		g = -0.031271 - (time * 4.53963e-07) + theta
		L = 4.900968 + (time * 3.67474e-07) + (math.sin(g) * (0.033434 - \
			2.3e-09 * time)) + (math.sin(2*g) * 0.000349) + theta
		eps = 23.440 - (time * 3.56e-07)
		ST = (6.720165 + 24.0 * (time / 365.25 - delta) + \
			0.000001411 * time) * (15.0 * math.pi / 180.0)

		if ST>(2*math.pi): ST=ST-(2*math.pi)

		# bnb: -180 < long < +180
		locst = ST + (long * math.pi/180.0) + 1.0027379 * (ahr + utc_lapse) \
			* (15.0 * math.pi /180.0)

		if locst>(2*math.pi): locst=locst-(2*math.pi)

		sinL = math.sin(L)
		X = math.cos(eps * math.pi /180.0) * sinL
		Y = math.cos(L)

		rasc = math.atan2(X,Y)

		if rasc<0.0: rasc=rasc+(2.0*math.pi)

		HA = rasc - locst
		sindec = math.sin(eps * math.pi /180.0) * sinL
		dec = math.asin(sindec)

		cosZ[hr] = ( math.sin(lat*math.pi/180.0) * sindec) + \
			(math.cos(lat*math.pi/180.0) * math.cos(math.asin(sindec)) * math.cos(HA))

		Z=math.acos(cosZ[hr])*180.0/math.pi
		I_O = (1367.0*(1+(.034*(math.cos(2.0*math.pi* \
			(((doy)-1.0)/365.0))))))

		#       ******* WHEN THE SOLAR ANGLE IS ABOVE THE HORIZON ********
		#       ******* WE START OUR CALCULATIONS ********

		if (I_O*cosZ[hr]>0):
			#       ****** CALCULATE SOLAR RADIATION FOR A SIX MINUTE PERIOD ********
			sun_top[ohour] = sun_top[ohour] + I_O*cosZ[hr]*0.1

		else:
			pass

	# *****CONVERTS Watts/m^2 to desired units *******
	for i in range(24):
		if sun_top[i]!=-99.00:
			if units == 1:
				sun_top[i] = sun_top[i] * 0.0861
			elif units == 2:
				sun_top[i] = sun_top[i] * 0.0036
			elif units == 3:
				pass
			elif units == 4:
				sun_top[i] = sun_top[i] * 0.316
	return sun_top

#----------------- TEST
nyear = 2012
mon = 6
#julian_day = 173 #jun 21
julian_day = 356 #dec 21
lat = 42
long = -77
utc_lapse = 5
units = 1
results = solar_top (nyear, mon, julian_day, lat, long, utc_lapse, units)
print "Hourly values:",results
sum = 0.
for i in range (len(results)):
	sum = sum + results[i]
print "Daily sum:",sum
