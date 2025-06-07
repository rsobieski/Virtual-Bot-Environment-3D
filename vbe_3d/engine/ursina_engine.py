from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING, List

from ursina import (
    Ursina, Entity, color, Vec3, Vec2, scene, destroy,
    DirectionalLight, Sky, Plane, AmbientLight,
    EditorCamera, camera, mouse, held_keys, input_handler, Text 
)

if TYPE_CHECKING:
    from vbe_3d.core.world import World


class ModelType:
    """Available 3D model types for objects."""
    CUBE = 'cube'
    SPHERE = 'sphere'
    CYLINDER = 'cylinder'
    CONE = 'cone'
    QUAD = 'quad'
    PLANE = 'plane'


class DebugInputHandler(Entity):
    """Debug input handler for logging key events."""

    def __init__(self):
        super().__init__()
        # Ensure it's parented to the camera to see if it moves with the camera
        # self.parent = camera
        print("Debug input handler initialized")

    def input(self, key):
        # This function is now correctly called by Ursina's event loop
        print(f"Debug: Key event detected - {key}")
        # Add a print to see if 'mouse' object itself is being updated
        # This can be very noisy if done frequently
        # print(f"Debug: Mouse position: {mouse.position}, Mouse delta: {mouse.delta}")

    def update(self):
        # Re-enable this if you want to see held keys, but it's not strictly necessary for camera control diagnosis
        # if held_keys:
        #     print(f"Debug: Currently held keys - {list(held_keys.keys())}")
        pass


class WorldUpdater(Entity):
    """An internal entity to manage the world's step function."""
    def __init__(self, world: 'World', engine: 'UrsinaEngine'):
        super().__init__()
        self.world = world
        self.engine = engine

    def update(self):
        try:
            self.world.step()
            for obj in list(self.engine.entities.keys()):
                self.engine.update_object(obj)
        except Exception as e:
            print(f"Error in simulation step: {e}")


class UrsinaEngine:
    """Ursina-based 3D visualization engine implementation.
    
    This engine uses Ursina (built on Panda3D) to provide 3D visualization
    capabilities for the simulation world.
    """

            
    def __init__(self, borderless: bool = False, enable_camera_controls: bool = True, debug: bool = True):
        """Initialize the Ursina engine.
        
        Args:
            borderless: Whether to run the window in borderless mode.
            enable_camera_controls: Whether to enable camera controls for user interaction.
            debug: Whether to enable debug logging for key presses.
        """       
        # Enable development mode for EditorCamera
        self.app = Ursina(borderless=borderless, development_mode=True)  # Add development_mode
        
        self.entities: Dict[Any, Entity] = {}
        self.debug = debug
        self.world_updater: Optional[WorldUpdater] = None
        self.editor_camera: Optional[EditorCamera] = None

        self._setup_scene()

        # Initialize debug AFTER camera setup
        if enable_camera_controls:
            self._setup_camera_controls()
            
        # Debug handler now created AFTER camera
        if self.debug:
            print("Initializing debug mode...")
            self.debug_handler = DebugInputHandler()


    def _setup_scene(self) -> None:
            """Set up the basic scene elements (lighting, sky, floor)."""
            self.ambient_light = AmbientLight(parent=scene, color=color.rgb(200, 200, 200))
            self.light = DirectionalLight(parent=scene, y=2, z=3, shadows=True, rotation=(45, -45, 0))
            self.light.look_at(Vec3(0, 0, 0))
            self.sky = Sky()
            
            # ground plane with 50% transparency
            self.ground = Entity(model='plane', scale=(100,1,100), color=color.gray.tint(-.2), texture='white_cube', texture_scale=(100,100), collider='box', alpha=0.5)
            self.floor = Plane(subdivisions=(32, 32))
            
            self.floor.rotation_x = 90
            self.floor.y = 0
            self.floor.scale = 100

            self.floor.color = color.gray.tint(-.2)
            self.floor.texture = 'white_cube'
            self.floor.texture_scale = (32, 32)
            
            # Add some debug text
            Text(text='Right Mouse: Rotate, Middle Mouse/Scroll: Zoom, Right Mouse + QWEASD: Move/Pan', position=(-0.85, 0.45))

        
    def _setup_camera_controls(self) -> None:
        """Set up camera controls for user interaction."""
        if self.editor_camera:
            destroy(self.editor_camera)
            self.editor_camera = None

        # Create EditorCamera with left mouse as pan key
        self.editor_camera = EditorCamera(
            rotation_speed=200,
            pan_speed=(0.5, 0.5),
            move_speed=10,
            zoom_speed=1.2,
            pan_key='left mouse'  # Add this to enable left mouse
        )

        # Properly parent camera to EditorCamera
        camera.parent = self.editor_camera
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)

        # Set initial position through EditorCamera
        self.editor_camera.position = (0, 10, -20)
        self.editor_camera.look_at(Vec3(0, 0, 0))

        print("Debug: EditorCamera initialized. Mouse visible:", 
              mouse.visible, "locked:", mouse.locked)

    def add_object(self, obj: Any) -> None:
        """Create a visual entity for the object in the Ursina scene."""
        try:
            pos = obj.position
            col = obj.color
        except AttributeError as e:
            raise AttributeError(f"Object must have position and color attributes: {e}")

        try:
            model_type = getattr(obj, 'model_type', ModelType.CUBE)
            scale = getattr(obj, 'scale', (1, 1, 1))

            entity = Entity(
                model=model_type,
                color=color.rgb(*[int(c * 255) for c in col]),
                position=pos,
                scale=scale,
                texture='white_cube',
                texture_scale=(1, 1)
            )

            self.entities[obj] = {
                'entity': entity,
                'model_type': model_type,
                'scale': scale
            }

        except Exception as e:
            raise RuntimeError(f"Failed to create entity for object: {e}")

    def remove_object(self, obj: Any) -> None:
        """Destroy the object's entity in the Ursina scene."""
        entity_data = self.entities.get(obj)
        if entity_data:
            destroy(entity_data['entity'])
            del self.entities[obj]

    def update_object(self, obj: Any) -> None:
        """Update the Ursina entity to match the object's state."""
        entity_data = self.entities.get(obj)
        if not entity_data:
            return

        try:
            entity = entity_data['entity']
            entity.position = obj.position
            entity.color = color.rgb(*[int(c * 255) for c in obj.color])

            if hasattr(obj, 'rotation'):
                rot = obj.rotation
                entity.rotation = Vec3(*rot) if isinstance(rot, (tuple, list)) else rot

            if hasattr(obj, 'scale'):
                new_scale = obj.scale
                if new_scale != entity_data['scale']:
                    entity.scale = new_scale
                    entity_data['scale'] = new_scale

            if hasattr(obj, 'model_type'):
                new_model = obj.model_type
                if new_model != entity_data['model_type']:
                    entity.model = new_model
                    entity_data['model_type'] = new_model

        except Exception as e:
            print(f"Warning: Failed to update object visualization: {e}")

    def run(self, world: 'World') -> None:
        """Begin the Ursina app loop, calling world.step() each frame."""
        self.world_updater = WorldUpdater(world, self)
        
        # Print status of EditorCamera and mouse just before running the app
        if self.editor_camera:
            print(f"Debug: EditorCamera active status: {self.editor_camera.enabled}")
        print(f"Debug: Mouse status before app.run() - visible: {mouse.visible}, locked: {mouse.locked}")

        self.app.run()

    def cleanup(self) -> None:
        """Clean up Ursina resources."""
        for entity_data in self.entities.values():
            destroy(entity_data['entity'])
        self.entities.clear()
        if hasattr(self, 'world_updater') and self.world_updater:
            destroy(self.world_updater)
            self.world_updater = None
        if hasattr(self, 'debug_handler') and self.debug_handler:
            destroy(self.debug_handler)
            self.debug_handler = None
        if hasattr(self, 'editor_camera') and self.editor_camera:
            destroy(self.editor_camera)
            self.editor_camera = None
        if hasattr(self, 'app'):
            self.app.destroy()