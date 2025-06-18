from sense_emu import SenseHat, ACTION_PRESSED
import time
import threading
from datetime import datetime
import requests

sense = SenseHat()
sense.clear()

light_threshold = float(input("Enter initial light threshold: "))
collision_threshold = 0.2
collision_state = False
light_on = False
power_state = "normal"
current_state = "normal"
in_setup_mode = False
last_input_time = 0
report_interval = 5 
last_orientation = sense.get_orientation()
flash_thread = None
stop_flashing = threading.Event()
SERVER_URL = "http://iotserver.com/report.php"

RED = (255, 0, 0)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)

def get_orientation_delta(prev, curr):
    return max(
        abs(round(prev['pitch'], 1) - round(curr['pitch'], 1)),
        abs(round(prev['roll'], 1) - round(curr['roll'], 1)),
        abs(round(prev['yaw'], 1) - round(curr['yaw'], 1))
    )

def flash_leds():
    while not stop_flashing.is_set():
        sense.clear(RED)
        time.sleep(0.5)
        sense.clear(OFF)
        time.sleep(0.5)

def handle_collision():
    global collision_state, flash_thread
    if not collision_state:
        collision_state = True
        print("Collision detected.")
        report_state(immediate=True)
        stop_flashing.clear()
        flash_thread = threading.Thread(target=flash_leds)
        flash_thread.start()

def clear_collision(event):
    global collision_state
    if event.action == ACTION_PRESSED and collision_state:
        print("Collision cleared manually.")
        collision_state = False
        stop_flashing.set()
        sense.clear()

def report_state(immediate=False):
    if in_setup_mode:
        return
    timestamp = datetime.now().isoformat()
    light = sense.get_humidity()
    power = sense.get_temperature()
    state = "collision" if collision_state else "normal"
    data = {
        "timestamp": timestamp,
        "light_level": round(light, 2),
        "power_level": round(power, 2),
        "collision_state": state,
        "power_state": power_state,
        "new_threshold": round(light_threshold, 2)
    }
    try:
        response = requests.post(SERVER_URL, json=data, timeout=5)
        print("Sent payload:", data)
        print("Server responded:", response.status_code, response.text)
        if response.status_code == 200:
            print("Report sent at", timestamp)
        else:
            print("Offline error: no acknowledgment.")
    except Exception as e:
        print("Offline error: server unreachable.", str(e))

def monitor_movement():
    global last_orientation
    time.sleep(1)
    while True:
        if in_setup_mode:
            time.sleep(0.5)
            continue
        curr_orientation = sense.get_orientation()
        delta = get_orientation_delta(last_orientation, curr_orientation)
        if delta > collision_threshold:
            handle_collision()
        elif not collision_state:
            current_state = "normal"
        last_orientation = curr_orientation
        time.sleep(0.2)

def periodic_report():
    while True:
        if not in_setup_mode:
            report_state()
        time.sleep(report_interval)

def streetlight_control():
    global light_on
    while True:
        if in_setup_mode or collision_state:
            time.sleep(0.5)
            continue
        light_level = sense.get_humidity()
        if power_state != "normal":
            sense.clear()
            light_on = False
        elif light_level < light_threshold and not light_on:
            sense.clear(WHITE)
            light_on = True
            print("Streetlight on. Humidity:", round(light_level, 1))
        elif light_level >= light_threshold and light_on:
            sense.clear()
            light_on = False
            print("Streetlight off. Humidity:", round(light_level, 1))
        time.sleep(0.5)

def monitor_power():
    global power_state, light_on
    while True:
        if in_setup_mode:
            time.sleep(0.5)
            continue
        power_level = sense.get_temperature()
        if power_level < 0:
            if power_state != "brownout":
                print("Brownout detected. Temperature:", round(power_level, 1))
            power_state = "brownout"
            sense.clear()
            light_on = False
        elif power_level > 100:
            if power_state != "surge":
                print("Power surge detected. Temperature:", round(power_level, 1))
            power_state = "surge"
            sense.clear()
            light_on = False
        else:
            if power_state != "normal":
                print("Power normalized. Temperature:", round(power_level, 1))
            power_state = "normal"
        time.sleep(0.5)

def show_threshold():
    message = f"Threshold: {int(light_threshold)}%"
    for char in message:
        sense.show_letter(char)
        time.sleep(0.2)
    sense.clear()

def adjust_threshold(change):
    global light_threshold, last_input_time
    light_threshold = max(0, min(100, light_threshold + change))
    last_input_time = time.time()
    show_threshold()

def enter_setup_mode(event):
    global in_setup_mode, last_input_time
    if event.action == ACTION_PRESSED and not collision_state:
        in_setup_mode = True
        last_input_time = time.time()
        sense.clear()
        print("Entered setup mode.")
        show_threshold()

def exit_setup_mode():
    global in_setup_mode
    in_setup_mode = False
    sense.clear()
    print("Exiting setup mode.")

def monitor_setup_timeout():
    global in_setup_mode
    while True:
        if in_setup_mode and time.time() - last_input_time > 10:
            print("Setup mode timed out.")
            exit_setup_mode()
        time.sleep(1)

sense.stick.direction_middle = enter_setup_mode
sense.stick.direction_up = lambda e: adjust_threshold(1) if in_setup_mode and e.action == ACTION_PRESSED else None
sense.stick.direction_down = lambda e: adjust_threshold(-1) if in_setup_mode and e.action == ACTION_PRESSED else None
sense.stick.direction_middle = lambda e: exit_setup_mode() if in_setup_mode and e.action == ACTION_PRESSED else clear_collision(e)

threads = [
    threading.Thread(target=monitor_movement, daemon=True),
    threading.Thread(target=periodic_report, daemon=True),
    threading.Thread(target=streetlight_control, daemon=True),
    threading.Thread(target=monitor_power, daemon=True),
    threading.Thread(target=monitor_setup_timeout, daemon=True),
]

for t in threads:
    t.start()

try:
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    sense.clear()
    print("Shutting down monitor.")
