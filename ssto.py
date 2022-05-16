import krpc
import time
import sys

try:
	conn = krpc.connect(address="voyevoda", name="SSTO flight assist")
	vessel = conn.space_center.active_vessel

	# telemetry streams
	ut = conn.add_stream(getattr, conn.space_center, "ut")
	altitude = conn.add_stream(getattr, vessel.flight(), "mean_altitude")
	apoapsis = conn.add_stream(getattr, vessel.orbit, "apoapsis_altitude")

	target_apoapsis = 80000

	# Pre-launch setup
	vessel.control.sas = True
	vessel.control.rcs = False
	vessel.control.throttle = 1.0
	vessel.control.brakes = True

	# Countdown...
	print('3...')
	time.sleep(1)
	print('2...')
	time.sleep(1)
	print('1...')
	time.sleep(1)

	vessel.control.brakes = False
	vessel.control.set_action_group(1, True)

	while altitude() < 75: # at takeoff
		pass

	print('Retracting gear')
	vessel.control.gear = False

	while altitude() < 16000: # at 16km
		pass

	print('Holding prograde')
	vessel.control.sas_mode = vessel.control.sas_mode.prograde
	
	while altitude() < 23000: # at 23km
		pass

	print('Switching engine')
	vessel.control.set_action_group(2, True)

	while apoapsis() < target_apoapsis:
		pass

	vessel.control.throttle = 0

	print('Coasting out of atmosphere')
	while altitude() < 70500:
	    pass

except KeyboardInterrupt:
	sys.exit()