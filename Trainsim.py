from ursina import *
import ollama
import threading
import time
import os
import random

app = Ursina()

# --- LIGHTING & SKY ---
Sky() 
# A directional light gives everything 3D shading and depth
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, 1))

# --- 3D ENVIRONMENT ---
# Using RGB for a more natural grass color
ground = Entity(model='plane', color=color.rgb(34, 139, 34), scale=(1000, 1, 1000), position=(0, -0.51, 0))

# Upgraded Tracks (Dark track bed + 2 silver rails)
track_bed = Entity(model='cube', color=color.rgb(50, 50, 50), scale=(2.6, 0.2, 1000), position=(0, -0.4, 0))
rail_left = Entity(model='cube', color=color.light_gray, scale=(0.2, 0.3, 1000), position=(-0.8, -0.15, 0))
rail_right = Entity(model='cube', color=color.light_gray, scale=(0.2, 0.3, 1000), position=(0.8, -0.15, 0))

# --- UPGRADED TRAIN (Multi-part Entity) ---
train = Entity(position=(0, 0, 0)) # The parent entity

# Boiler/Body (Black cylinder)
Entity(parent=train, model='cylinder', color=color.black, scale=(1.4, 4, 1.4), rotation=(90, 0, 0), position=(0, 1, 1))
# Cabin (Red box)
Entity(parent=train, model='cube', color=color.rgb(178, 34, 34), scale=(1.8, 2.5, 2.2), position=(0, 1.5, -1.5))
# Roof (Dark gray overhang)
Entity(parent=train, model='cube', color=color.dark_gray, scale=(2.0, 0.2, 2.4), position=(0, 2.8, -1.5))
# Smokestack
Entity(parent=train, model='cylinder', color=color.dark_gray, scale=(0.4, 1, 0.4), position=(0, 2, 2.2))
# Headlight
Entity(parent=train, model='sphere', color=color.yellow, scale=(0.6, 0.6, 0.6), position=(0, 1, 3.1))
# Cowcatcher (Front bumper)
Entity(parent=train, model='cube', color=color.gray, scale=(2, 0.5, 1), position=(0, 0.5, 3.2))

# --- STATION ---
station_platform = Entity(model='cube', color=color.light_gray, scale=(8, 1, 30), position=(6, 0, 150))
station_building = Entity(model='cube', color=color.orange, scale=(6, 4, 20), position=(6, 2.5, 150))

# --- SCENERY ---
for i in range(60):
    z_pos = random.uniform(20, 800)
    x_pos = random.choice([random.uniform(12, 30), random.uniform(-30, -10)])
    
    tree_trunk = Entity(model='cube', color=color.brown, scale=(0.5, 2, 0.5), position=(x_pos, 0.5, z_pos))
    tree_leaves = Entity(parent=tree_trunk, model='cube', color=color.green, scale=(4, 3, 4), y=1)

# --- UI ELEMENTS ---
dispatch_text = Text(text="Press 'T' to contact AI Dispatcher", position=(-0.85, 0.45), scale=1.5, color=color.yellow)
speed_text = Text(text="Speed: 0 mph", position=(-0.85, 0.40), scale=1.5, color=color.white)
camera_text = Text(text="Press 'C' to change camera", position=(-0.85, 0.35), scale=1.5, color=color.cyan)
distance_text = Text(text="Distance to Station: --", position=(-0.85, 0.30), scale=1.5, color=color.light_gray)

is_fetching_message = False

# --- AI THREAD FUNCTION ---
def fetch_ai_message(current_velocity, distance):
    global is_fetching_message
    is_fetching_message = True
    dispatch_text.text = "Contacting Dispatcher (Llama 3.2)..."
    
    state = "stopped"
    if current_velocity > 0.05: state = "moving forward"
    elif current_velocity < -0.05: state = "reversing"
    
    mph = abs(int(current_velocity * 100))

    prompt = f"You are a gritty train dispatcher. The train is {state}, traveling at {mph} mph, and is {int(distance)} meters away from the station. Give a short, realistic 1-sentence radio instruction to the engineer. No pleasantries. Do not use quotes."
    
    try:
        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        msg = response['message']['content'].strip()
        
        dispatch_text.text = f"DISPATCH: {msg}"
        os.system(f'say -v "Alex" "{msg}" &')
        
    except Exception as e:
        dispatch_text.text = f"ERROR: Make sure Ollama is running!"
        print(e)
    
    time.sleep(5)
    is_fetching_message = False

# --- PHYSICS & CAMERA VARIABLES ---
velocity = 0
acceleration = 0.5
friction = 0.98 
camera_view = 1 

def input(key):
    global camera_view
    if key == 'c':
        camera_view = 1 if camera_view == 2 else 2

# --- MAIN GAME LOOP ---
def update():
    global velocity
    
    if held_keys['w']:
        velocity += acceleration * time.dt
    if held_keys['s']:
        velocity -= acceleration * time.dt
        
    velocity *= friction
    train.z += velocity
    
    # Update Camera Position
    if camera_view == 1:
        # 3rd Person View
        camera.position = (train.x + 8, train.y + 6, train.z - 15)
        camera.look_at(train)
    else:
        # 1st Person View (Shifted slightly forward to see out of the new cabin)
        camera.position = (train.x, train.y + 2, train.z + 1.5)
        camera.rotation = (0, 0, 0)
    
    # Calculate Telemetry
    mph = abs(int(velocity * 100))
    distance_to_station = station_platform.z - train.z
    
    # Update UI
    speed_text.text = f"Speed: {mph} mph"
    if distance_to_station > 0:
        distance_text.text = f"Distance: {int(distance_to_station)} m"
    else:
        distance_text.text = "Station Passed!"
        
    # Trigger AI
    if held_keys['t'] and not is_fetching_message:
        threading.Thread(target=fetch_ai_message, args=(velocity, distance_to_station)).start()

    if held_keys['escape']:
        application.quit()

app.run()