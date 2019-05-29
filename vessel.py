from __future__ import print_function
import krpc
import time
import numpy as np



class Ship:
    def __init__(self, client_name):
        self.conn = krpc.connect(client_name)
        self.vessel = self.conn.space_center.active_vessel
        self.timer = 0 # Status print interval timer init
        self.interval = 200  # Staus print interval
        self.orbital_insertion_burn = 20 # Estimated time for circurulisation  burn

    def launch_to_orbit(self, orbit_height):
        # Notes for successful launch
        # - Engine ignitions on first stage with appropriate thrust limter #TODO dynamic thrust inflight
        # - Launch clamps on second stage with fuel pumps enabled
        # - Fairing seperation on third stage
        # - Main booster decoupler on fourth stage
        # - Ullage boosters on fifth stage
        # - Vacume engine for apoapsis burn on sixth stage
        # - Vessel will go onto a prograde equatorial orbit

        # Initiating auto pilot
        self.vessel.auto_pilot.target_pitch_and_heading(90, 90)
        self.vessel.auto_pilot.engage()

        # Igniting booster stage
        self.vessel.control.throttle = 1
        self.vessel.control.activate_next_stage()
        print("Ignition")

        # waiting for booster engines to stabilaze fuel flow and gain thrust
        time.sleep(1)

        # launch clamp staging
        self.vessel.control.activate_next_stage() 
        print("Liftoff")

        # Ascent burn
        while self.vessel.orbit.apoapsis_altitude < orbit_height: 
            
            # Establishing parameters for suborbital flight
            vessel_alt = self.vessel.flight().mean_altitude
            apoapsis_alt = self.vessel.orbit.apoapsis_altitude
            vessel_pitch = ascent_profile(vessel_alt)

            # Holding pitch for gravity turn
            self.vessel.auto_pilot.target_pitch_and_heading(vessel_pitch, 270)

            # Status print
            self.status(["vessel_alt", "vessel_pitch", "apoapsis_alt"])

        # Main booster cutoff
        self.vessel.control.throttle = 0
        print("\nTarget apoapsis reached, coasting to space")

        # Waiting for vessel to reach orbit
        while self.vessel.flight().mean_altitude < 70000:
            self.status("vessel_alt")

        # Reached space
        print("\nReached space, deploying extra atmospheric instruments")

        # Fairng seperation
        self.vessel.control.activate_next_stage()

        # Extra atmospheric instruments action group
        self.vessel.control.toggle_action_group(1)
        self.vessel.control.rcs = True
        
        time.sleep(0.5)
        self.vessel.control.activate_next_stage() # Main booster separation
        print("Main booster separetion")

        # Waiting for orbital insertion 
        while self.vessel.orbit.time_to_apoapsis > self.orbital_insertion_burn / 2:
            self.status(["time_to_aps", "time_to_burn"], time_to_burn=self.vessel.orbit.time_to_apoapsis - self.orbital_insertion_burn / 2)
            self.vessel.auto_pilot.target_pitch_and_heading(180, 270)
        
        # Orbital Insertion burn
        self.vessel.control.throttle = 1
        self.vessel.control.activate_next_stage() # Ullage burn
        print("\nPerforming ullage burn")
        time.sleep(0.5)
        self.vessel.control.activate_next_stage() # Second stage ignition #TODO add ullage
        print("Performing orbital insertion")
        while self.vessel.orbit.periapsis_altitude < orbit_height - 10000:
            self.status(["apoapsis_alt", "periapsis_alt"])
            self.vessel.auto_pilot.target_pitch_and_heading(180, 270)
    
        self.vessel.control.throttle = 0
        #self.vessel.control.activate_next_stage() # Abort system detatchement
        print(f"\nSuccesful orbital insertion with an apoapsis of {int(self.vessel.orbit.apoapsis_altitude)} meters and periapsis of {int(self.vessel.orbit.periapsis_altitude)} meters")
        
        # Deploying payload
        time.sleep(2)
        self.vessel.control.activate_next_stage()
        print("Payload succesfully deployed")

        input()


    # Funciton for printng vessel parameters
    def status(self, parameters, time_to_burn=0):
        if self.timer == 0:
            lines = 0
            status_out = ""
            if "vessel_alt" in parameters: # TODO Add switch statement in for loop
                status_out += f"Vessel Altitude: {int(self.vessel.flight().mean_altitude)} meters | "

            if "vessel_pitch" in parameters:
                status_out += f"Vessel Pitch: {int(ascent_profile(self.vessel.flight().mean_altitude))} degrees | "
            
            if "apoapsis_alt" in parameters:
                status_out += f"Apoapsis Altitude: {int(self.vessel.orbit.apoapsis_altitude)} meters | "
            
            if "periapsis_alt" in parameters:
                status_out += f"Periapsis Altitude: {int(self.vessel.orbit.periapsis_altitude)} meters | "
            
            if "time_to_aps" in parameters:
                status_out += f"Time to apoapsis: {int(self.vessel.orbit.time_to_apoapsis)} seconds | "
            
            if "time_to_burn" in parameters:
                status_out += f"Engine Ignition in T - {int(time_to_burn)} seconds | "
            
            
            if status_out:
                print(status_out, end="\r")
        
        self.timer += 1
        self.timer %= self.interval

def ascent_profile(height): # Determines pitch angle based on height for gravity turn
    return 180 - 90 * np.exp((-height) / 20000.0) # lower denominator => steeper turn


def run():
    ship = Ship("Delta IV")
    ship.launch_to_orbit(90000)

run()

    