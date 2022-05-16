import time
import krpc
import sys
import math

try:
	conn = krpc.connect(address="localhost", name='Perform hoverslam')
	vessel = conn.space_center.active_vessel

	# set up streams
	altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
	retrograde = conn.add_stream(getattr, vessel.flight(), 'retrograde')
	prograde = conn.add_stream(getattr, vessel.flight(), 'prograde')

	reference_frame = vessel.orbit.body.reference_frame
	v_speed = conn.add_stream(getattr, vessel.flight(reference_frame), 'vertical_speed')
	h_speed = conn.add_stream(getattr, vessel.flight(reference_frame), 'horizontal_speed')
	speed = conn.add_stream(getattr, vessel.flight(reference_frame), 'speed')

	# pre-launch setup
	vessel.control.sas = False
	vessel.control.rcs = True
	vessel.control.throttle = 1.0

	# countdown
	print('3...')
	time.sleep(1)
	print('2...')
	time.sleep(1)
	print('1...')
	time.sleep(1)
	print('Launch')

	# launch the rocket up for testing
	vessel.control.activate_next_stage()
	vessel.auto_pilot.engage()
	vessel.auto_pilot.target_pitch_and_heading(90, 90)
	time.sleep(2)
	
	vessel.control.gear = False
	vessel.auto_pilot.target_pitch_and_heading(50, 90)
	time.sleep(2)

	vessel.control.throttle = 0.0
	vessel.auto_pilot.disengage()
	vessel.control.sas = True
	vessel.control.sas_mode = vessel.control.sas_mode.stability_assist
	time.sleep(0.5)

	# perform a hoverslam
	print('Waiting until the vessel is falling')
	while v_speed() >= -1:
		time.sleep(0.1)

	print('Facing retrograde')
	vessel.control.sas_mode = vessel.control.sas_mode.retrograde
	vessel.control.gear = True
	vessel.control.brakes = True
	time.sleep(3)

	print('Waiting to burn')

	x = 0
	fall_distance = 0

	offset = ( vessel.mass * speed() ) / 25000 - ( vessel.mass / 1000 )
	print(f'offset: {offset:.2f}')

	while fall_distance - offset > x or fall_distance == 0:
		if vessel.situation == vessel.situation.landed:
			break

		fall_distance = 0
		while fall_distance < 20:
			ray_origin = vessel.bounding_box(reference_frame)[0]
			fall_distance = abs(conn.space_center.raycast_distance(ray_origin, prograde(), reference_frame))

		# apply the tsiolkovsky rocket equation
		F = vessel.available_thrust						# thrust
		Isp = vessel.specific_impulse * 9.82			# specific impulse
		if Isp == 0:
			sys.exit()
		m0 = vessel.mass								# mass before burn
		m1 = m0 / math.exp(( abs(speed()) + 0.01 )/Isp) # mass after burn

		a = F / ( (m0 + m1) / 2 ) - 9.82 	# acceleration = thrust / mass - g
		x = 0.5 * ( speed() ** 2 / a )		# distance to stop = 1/2 * v²/a

	print('Burning')
	vessel.control.throttle = 1.0 	# simulates the limits of real rocket engines
									# does not throttle below 100%
	while v_speed() < -10 and vessel.situation != vessel.situation.landed:
		pass

	print('Holding attitude')
	vessel.control.sas_mode = vessel.control.sas_mode.stability_assist

	while v_speed() < 0:
		pass

	vessel.control.throttle = 0.0
	print(f'MECO at {altitude():.2f}m elevation')

	time.sleep(3)
	vessel.control.brakes = False
	vessel.control.sas = False
	vessel.control.rcs = False

	print('Landed!')

except KeyboardInterrupt:
	sys.exit()