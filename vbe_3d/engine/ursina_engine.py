from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from ursina import Ursina, Entity, color, Vec3, scene, destroy

from .base import Engine

# Engine Ursina (Panda3D)

if TYPE_CHECKING:  # forward import only for typing
    from vbe_3d.core.world import World


class UrsinaEngine(Engine):
    """Ursina-based 3D visualization engine implementation.
    
    This engine uses Ursina (built on Panda3D) to provide 3D visualization
    capabilities for the simulation world.
    """
    
    def __init__(self, borderless: bool = False):
        """Initialize the Ursina engine.
        
        Args:
            borderless: Whether to run the window in borderless mode.
        """
        self.app = Ursina(borderless=borderless)
        self.entities: Dict[Any, Entity] = {}
        self._setup_scene()
        
    def _setup_scene(self) -> None:
        """Set up the basic scene elements (lighting, sky, floor)."""
        from ursina import DirectionalLight, Sky, Plane, AmbientLight
        
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

    def add_object(self, obj: Any) -> None:
        """Create a visual entity for the object in the Ursina scene.
        
        Args:
            obj: The simulation object to visualize. Must have position and color attributes.
            
        Raises:
            AttributeError: If the object is missing required attributes.
        """
        try:
            pos = obj.position
            col = obj.color
        except AttributeError as e:
            raise AttributeError(f"Object must have position and color attributes: {e}")
            
        try:
            cube = Entity(
                model='cube',
                color=color.rgb(*[int(c*255) for c in col]),
                position=pos,
                scale=(1,1,1),
                texture='white_cube',
                texture_scale=(1,1)
            )
            self.entities[obj] = cube
        except Exception as e:
            raise RuntimeError(f"Failed to create entity for object: {e}")

    def remove_object(self, obj: Any) -> None:
        """Destroy the object's entity in the Ursina scene.
        
        Args:
            obj: The simulation object whose visualization should be removed.
        """
        ent = self.entities.get(obj)
        if ent:
            destroy(ent)
            del self.entities[obj]

    def update_object(self, obj: Any) -> None:
        """Update the Ursina entity to match the object's state.
        
        Args:
            obj: The simulation object whose visualization should be updated.
        """
        ent = self.entities.get(obj)
        if not ent:
            return
            
        try:
            pos = obj.position
            ent.position = pos
            
            col = obj.color
            ent.color = color.rgb(*[int(c*255) for c in col])
            
            # Update rotation if available
            if hasattr(obj, 'rotation'):
                ent.rotation = obj.rotation
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
        for ent in self.entities.values():
            destroy(ent)
        self.entities.clear()
        if hasattr(self, 'app'):
            self.app.destroy()
