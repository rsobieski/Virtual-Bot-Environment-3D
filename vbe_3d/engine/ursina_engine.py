from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING, List

from ursina import (
    Ursina, Entity, color, Vec3, Vec2, scene, destroy,
    DirectionalLight, Sky, Plane, AmbientLight,
    EditorCamera, camera, mouse, held_keys, input_handler
)

from .base import Engine

# Engine Ursina (Panda3D)

if TYPE_CHECKING:  # forward import only for typing
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
        print("Debug input handler initialized")
        
    def input(self, key):
        print(f"Debug: Key event detected - {key}")
        
    def update(self):
        if held_keys:
            print(f"Debug: Currently held keys - {list(held_keys.keys())}")


class UrsinaEngine(Engine):
    """Ursina-based 3D visualization engine implementation.
    
    This engine uses Ursina (built on Panda3D) to provide 3D visualization
    capabilities for the simulation world.
    """
    
    def __init__(self, borderless: bool = False, enable_camera_controls: bool = True, debug: bool = False):
        """Initialize the Ursina engine.
        
        Args:
            borderless: Whether to run the window in borderless mode.
            enable_camera_controls: Whether to enable camera controls for user interaction.
            debug: Whether to enable debug logging for key presses.
        """
        self.app = Ursina(borderless=borderless)
        self.entities: Dict[Any, Entity] = {}
        self.debug = debug
        
        # Initialize debug input handler if debug is enabled
        if self.debug:
            print("Initializing debug mode...")
            self.debug_handler = DebugInputHandler()
            
        self._setup_scene()
        
        # Enable camera controls if requested
        if enable_camera_controls:
            self._setup_camera_controls()
        
    def _setup_scene(self) -> None:
        """Set up the basic scene elements (lighting, sky, floor)."""
        # Add ambient light for better overall illumination
        self.ambient_light = AmbientLight(parent=scene, color=color.rgb(200, 200, 200))
        
        # Add directional light for shadows and depth
        self.light = DirectionalLight(parent=scene, y=2, z=3, shadows=True, rotation=(45, -45, 0))
        self.light.look_at(Vec3(0, 0, 0))
        
        # Add sky for background
        self.sky = Sky()
        
        # Add floor plane
        self.floor = Plane(subdivisions=(32,32))
        self.floor.color = color.gray.tint(-.2)
        self.floor.texture = 'white_cube'
        self.floor.texture_scale = (32,32)
        
    def _setup_camera_controls(self) -> None:
        """Set up camera controls for user interaction."""
        # Create editor camera for free movement
        self.editor_camera = EditorCamera()
        
        # Configure camera controls
        self.editor_camera.rotation_speed = 200  # Adjust rotation speed
        self.editor_camera.pan_speed = (0.5, 0.5)  # Adjust pan speed (x, y)
        self.editor_camera.move_speed = 10      # Adjust movement speed
        self.editor_camera.zoom_speed = 0.5     # Adjust zoom speed
        
        # Set initial camera position and target
        camera.position = (0, 10, -20)
        camera.look_at(Vec3(0, 0, 0))
        
        # Enable mouse controls
        mouse.visible = True
        mouse.locked = False  # Allow mouse to move freely
        
        # Set up camera control keys
        self.editor_camera.keys = {
            'forward': 'w',
            'backward': 's',
            'left': 'a',
            'right': 'd',
            'up': 'e',
            'down': 'q',
            'rotate_left': 'arrow_left',
            'rotate_right': 'arrow_right',
            'rotate_up': 'arrow_up',
            'rotate_down': 'arrow_down',
            'pan_left': 'j',
            'pan_right': 'l',
            'pan_up': 'i',
            'pan_down': 'k',
            'zoom_in': 'mouse1',
            'zoom_out': 'mouse2',
            'rotate': 'mouse3',
            'pan': 'mouse2'
        }

    def add_object(self, obj: Any) -> None:
        """Create a visual entity for the object in the Ursina scene.
        
        Args:
            obj: The simulation object to visualize. Must have position and color attributes.
                Can optionally have model_type and scale attributes.
            
        Raises:
            AttributeError: If the object is missing required attributes.
        """
        try:
            pos = obj.position
            col = obj.color
        except AttributeError as e:
            raise AttributeError(f"Object must have position and color attributes: {e}")
            
        try:
            # Get model type and scale from object if available
            model_type = getattr(obj, 'model_type', ModelType.CUBE)
            scale = getattr(obj, 'scale', (1, 1, 1))
            
            # Create entity with specified model
            entity = Entity(
                model=model_type,
                color=color.rgb(*[int(c*255) for c in col]),
                position=pos,
                scale=scale,
                texture='white_cube',
                texture_scale=(1,1)
            )
            
            # Store entity and its properties
            self.entities[obj] = {
                'entity': entity,
                'model_type': model_type,
                'scale': scale
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to create entity for object: {e}")

    def remove_object(self, obj: Any) -> None:
        """Destroy the object's entity in the Ursina scene.
        
        Args:
            obj: The simulation object whose visualization should be removed.
        """
        entity_data = self.entities.get(obj)
        if entity_data:
            destroy(entity_data['entity'])
            del self.entities[obj]

    def update_object(self, obj: Any) -> None:
        """Update the Ursina entity to match the object's state.
        
        Args:
            obj: The simulation object whose visualization should be updated.
        """
        entity_data = self.entities.get(obj)
        if not entity_data:
            return
            
        try:
            entity = entity_data['entity']
            
            # Update position
            pos = obj.position
            entity.position = pos
            
            # Update color
            col = obj.color
            entity.color = color.rgb(*[int(c*255) for c in col])
            
            # Update rotation if available
            if hasattr(obj, 'rotation'):
                rot = obj.rotation
                if isinstance(rot, (tuple, list)) and len(rot) == 3:
                    entity.rotation = Vec3(*rot)
                elif isinstance(rot, Vec3):
                    entity.rotation = rot
                    
            # Update scale if changed
            if hasattr(obj, 'scale'):
                new_scale = obj.scale
                if new_scale != entity_data['scale']:
                    entity.scale = new_scale
                    entity_data['scale'] = new_scale
                    
            # Update model type if changed
            if hasattr(obj, 'model_type'):
                new_model = obj.model_type
                if new_model != entity_data['model_type']:
                    entity.model = new_model
                    entity_data['model_type'] = new_model
                    
        except Exception as e:
            print(f"Warning: Failed to update object visualization: {e}")

    def run(self, world: 'World') -> None:
        """Begin the Ursina app loop, calling world.step() each frame.
        
        Args:
            world: The simulation world to visualize.
        """
        def update():
            try:
                world.step()
                for obj in list(self.entities.keys()):
                    self.update_object(obj)
            except Exception as e:
                print(f"Error in simulation step: {e}")
                
        self.app.taskMgr.add(lambda task: (update() or True) and task.cont, "world_update_task")
        self.app.run()
        
    def cleanup(self) -> None:
        """Clean up Ursina resources."""
        for entity_data in self.entities.values():
            destroy(entity_data['entity'])
        self.entities.clear()
        if hasattr(self, 'app'):
            self.app.destroy()
