from typing import Any, Dict, TYPE_CHECKING

from ursina import Ursina, Entity, color, Vec3, scene

from .base import Engine

# Engine Ursina (Panda3D)

if TYPE_CHECKING:  # forward import only for typing
    from vbe_3d.core.world import World


class UrsinaEngine(Engine):
    def __init__(self):
        # Initialize the Ursina app
        self.app = Ursina(borderless=False)  # borderless False to allow window controls (just a setting)
        self.entities: Dict[Any, Entity] = {}  # map simulation objects to Ursina Entities
        # Add ambient lighting and a floor plane
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
        self.floor.color = color.gray.tint(-.2)  # Slightly darker gray
        self.floor.texture = 'white_cube'
        self.floor.texture_scale = (32,32)

    def add_object(self, obj: Any) -> None:
        """Create a cube entity for the object in the Ursina scene."""
        # assume the object has at least properties: position (x,y,z) and color (RGB tuple)
        pos = obj.position
        col = obj.color  # expecting a color tuple like (r,g,b) in [0,1] range
        cube = Entity(
            model='cube',
            color=color.rgb(*[int(c*255) for c in col]),
            position=pos,
            scale=(1,1,1),
            texture='white_cube',  # Add texture for better visual appearance
            texture_scale=(1,1)    # Scale texture appropriately
        )
        self.entities[obj] = cube

    def remove_object(self, obj: Any) -> None:
        """Destroy the object's entity in the Ursina scene."""
        ent = self.entities.get(obj)
        if ent:
            from ursina import destroy
            destroy(ent)
            del self.entities[obj]

    def update_object(self, obj: Any) -> None:
        """Update the Ursina entity to match the object's state (position, color, etc.)."""
        ent = self.entities.get(obj)
        if not ent:
            return
        pos = obj.position
        ent.position = pos
        # Update color if the object's color might change
        col = obj.color
        ent.color = color.rgb(*[int(c*255) for c in col])
        # TODO: update other properties like orientation 

    def run(self, world: Any) -> None:
        """Begin the Ursina app loop, calling world.step() each frame."""
        # Define an update function that Ursina will call every frame
        def update():
            world.step()  # advance the simulation by one step (tick)
            # After stepping logic, update all objects' visuals
            for obj in list(self.entities.keys()):
                self.update_object(obj)
        # Assign the update function into the Ursina app's namespace
        # Ursina will call a global update() if present. We ensure our 'update' is known.
        self.app.taskMgr.add(lambda task: (update() or True) and task.cont, "world_update_task")
        # Above, we use Panda3D's task manager via Ursina to call update continuously.
        # the Ursina main loop (open the window and start rendering)
        self.app.run()
