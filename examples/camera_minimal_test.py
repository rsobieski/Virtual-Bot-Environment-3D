from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina(development_mode=True)
Sky()  # Add a sky background

# Add a ground plane with 50% transparency
ground = Entity(model='plane', scale=(100,1,100), color=color.gray.tint(-.2), texture='white_cube', texture_scale=(100,100), collider='box', alpha=0.5)

# # Use FirstPersonController instead of EditorCamera
player = FirstPersonController()
player.position = (0, 2, 0)  # Start slightly above ground

# Setup camera with mouse controls
camera = EditorCamera()
camera.position = (0, 5, -10)  # Start position
camera.rotation = (0, 0, 0)    # Start rotation

# Configure mouse controls
camera.rotation_speed = 200    # Adjust rotation speed
camera.pan_speed = (1, 1)     # Adjust pan speed (x, y)
camera.zoom_speed = 10        # Adjust zoom speed

# Add some debug text
Text(text='Left Mouse: Rotate, Middle Mouse/Scroll: Zoom, Right Mouse: Pan', position=(-0.85, 0.45))

# Add a simple cube to help with orientation
cube = Entity(model='cube', color=color.red, position=(5, 0.5, 5))

app.run()