# Virtual Bot Environment 3D 

*A modular 3‑D simulation playground for for self-managing bots*

Virtual Bot Environment 3D lets you build a real‑time simulation where autonomous **cube bots** ("cells") move, learn, negotiate, reproduce and cooperate.  Each robot (bot) carries its own pluggable **DNA/brain** — either static rule‑based logic or a neural‑network policy trained online with reinforcement learning.

The framework is written in Python, is intended to be designed as fully open‑source‑friendly, and wraps all heavy external libraries behind clean interfaces so you can swap them at will (graphics engine, physics backend, RL algorithm, etc.).

This is an experimental project in which I wanted to bring together several concepts I've recently had the opportunity to work with and explore. For simplicity, this version uses cube-based bots for visualization, which might resemble Minecraft, but that's merely a superficial similarity resulting from the ease of presenting the environment.

---
## Key Features:

|  Category               |  Highlights                                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Real‑time 3‑D**       | Uses an `Engine` abstraction. Default implementation = **Ursina/Panda3D** (desktop) ready for future WebGL engine. |
| **Intelligent robots**  | Each robot owns a **RobotBrain**.  Choose `RuleBasedBrain`, `RLBrain` (PyTorch MLP/CNN), or plug‑in your own.      |
| **Genetic evolution**   | Robots can clone or create offspring by **mixing their DNA** (traits & NN weights).                                |
| **Dynamic connections** | 5‑level bond strength (`NONE → PERMANENT`). Robots connect/disconnect on proximity & negotiation hooks.            |
| **Online RL**           | Supports on‑the‑fly policy updates (DQN/PPO via Stable‑Baselines3) while the world is running.                     |
| **Persistence**         | Save / load the entire world state as JSON — resume long simulations or share scenarios.                           |
| **Swappable parts**     | Swap 3‑D engines, brains, physics, or genetics without touching *core* logic.                                      |
| **Unified Configuration** | JSON-based configuration system for both engines — easily experiment with different world setups and robot behaviors. |

---
## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/rsobieski/Virtual-Bot-Environment-3D.git
cd Virtual-Bot-Environment-3D

# Create and activate virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

The main dependencies include:
- **Ursina** - 3D game engine for desktop visualization
- **PyTorch** - Deep learning framework for RL brains
- **NumPy** - Numerical computing
- **WebSockets** - For WebGL communication

For a complete list, see `requirements.txt`.

---
## Project Structure

```
3D-Virtual-Bot-Environment/
├── vbe_3d/                    # Main package
│   ├── brain/                 # Robot brain implementations
│   │   ├── base_brain.py      # Abstract brain interface
│   │   ├── rule_based.py      # Rule-based behavior
│   │   ├── rl_brain.py        # Reinforcement learning brain
│   │   └── factory.py         # Brain factory
│   ├── core/                  # Core simulation components
│   │   ├── world.py           # Main world container
│   │   ├── robot.py           # Robot agent class
│   │   ├── static_element.py  # Resource/obstacle elements
│   │   └── base_element.py    # Base element class
│   ├── engine/                # Visualization engines
│   │   ├── base.py            # Engine abstraction
│   │   ├── ursina_engine.py   # Desktop 3D engine
│   │   └── webgl_engine.py    # WebGL engine
│   └── utils/                 # Utility functions
├── examples/                  # Example scripts and configs
│   ├── run_demo.py            # Basic demo
│   ├── run_with_config.py     # Configurable demo
│   ├── world_config.json      # Basic configuration
│   ├── advanced_world_config.json
│   └── web_visualization/     # WebGL examples
└── requirements.txt           # Python dependencies
```

---
## Architecture Overview:

The library is structured into several core components for transparency and collaborative development:

* **World and Engine:** The World class represents the simulation world or "scene". It contains all objects (robots, resources, etc.), handles the global simulation loop (advancing time steps), and manages interactions like checking distances for connections or triggering events. The World uses an **Engine** (abstraction for the 3D engine) to create and render objects. The Engine interface defines methods for adding an object (e.g., spawning a cube in the 3D scene), removing an object, and updating object transformations (position, color, etc.) each frame. 

* **Robot (Dynamic Element):** The Robot class (a subclass of a generic BaseElement) represents an active agent in the world. Each robot should has:
    * Properties/State: e.g. position in the world, velocity, energy level, color, unique ID, and possibly a "goal" or imperative defining its objective.
    * Connections: a record of links to other robots with a certain strength level. It is define as a numeric level for connection strength (0 = none, 1 = weak, 2 = medium, 3 = strong, 4 = permanent). Robots can form connections when in proximity, and these can strengthen over time or break if they separate. (In this version, it is implement a basic proximity-based connection; the framework allows extending this to more complex bonding behavior and negotiation protocols).
    * Robot State: it is define current state of robot, we have here enum to track it (IDLE, MOVING, COLLECTING, REPRODUCING, DEAD) and dataclass for tracking it.
    * Brain/Logic: Each robot has a RobotBrain component that decides its actions. This could be a simple rule-based brain (pre-programmed behavior) or a learned brain (RL policy network). The robot's "intelligence" is thus pluggable – one can equip different robots with different brains. This also allows hybrid scenarios where some robots are manually scripted and others learn via ML. Additional models are planned for future versions/

* **Static Element:** We also define a StaticElement (or Resource) class for objects in the world that are not agents – for example, a resource block that a robot can utilize (like an energy source or building material). Static elements have properties (like amount of resource) and basic logic (they might do nothing on their own, or have simple rules like "decrease resource when a robot takes it"). They inherit from the same base class as Robot but typically have no active brain (or a no-op brain). This keeps the environment extensible – eventually, even these could be given ML models for more complex behavior, but by default they remain simple.

* **Robot Brain (Behavior controllers):** - design a hierarchy for robot "brains":
    * RobotBrain is an abstract base defining the interface (at minimum, a method like decide_action(observation)).
    * RuleBasedBrain (or SimpleBrain) implements a fixed behavior strategy (for example, move randomly, or follow a specific pattern/rule such as "if a resource is nearby, move toward it, else wander"). This is used for static logic or to provide baseline behaviors.
    * RLBrain implements a brain controlled by a neural network (with potential for learning). It contains a PyTorch model (which could include dense layers or CNN layers) that outputs actions given the robot's observation of the world. The RLBrain can also include methods to train the model via reinforcement learning. In this initial version, there is not fully implement a training loop, but outline how training: e.g., using reward signals based on goals (provided by the environment or the robot's imperative), and optimization via an RL algorithm. I keep the training logic modular – one could use Stable-Baselines3 to train outside the simulation loop by treating the World as an environment, or implement a custom training loop that calls world.step() repeatedly and updates the RLBrain network weights online (on-the-fly).
    * (In the future, one could add other brain types, like a GeneticBrain using evolutionary algorithms, etc., which is why a polymorphic design is helpful.)

* **Interaction and Negotiation:** The framework will handle interactions between robots. In each simulation step, after robots take their individual actions, the World checks for interactions:
    * Collisions/Proximity: If two robots (or a robot and a static element) come within a certain distance, we trigger an interaction. For robots, this could mean forming or strengthening a connection (if they are "compatible" to connect based on their types/properties). We maintain each robot's connections in a list or dict. Negotiation for connection or movement (e.g., if two robots want to occupy the same space) can be implemented by comparing their properties or "intentions" – in a simple case, we might randomly decide which one yields, or have a priority rule (like larger robot pushes smaller one). In this initial prototype, we will implement basic rules (like not allowing two robots to overlap; one might stop if another is in its way, etc.) and leave a hook for more complex negotiation (for example, exchanging messages or a mini-game to decide who moves first – this could be an area of future ML training for cooperative behavior).
    * Resource Interaction: If a robot is adjacent to a resource block, it might "consume" it (gain energy, and the resource reduces or disappears). There is implement an example rule for this ( robot's energy increases and the static element is removed from the world).
    * Collective Goals: The design allows scenarios where robots must cooperate to achieve something (e.g., assemble into a larger structure to move). We can simulate a simple scenario like two half-robots connecting to form a bigger robot. Such complex interactions will involve goal assignments and possibly multi-agent reinforcement learning. This framework is ready for this: we can specify a goal for each robot or a global goal and incorporate that into the reward function for RL brains, encouraging teamwork.

* **Reproduction and Evolution (DNA):** Robots can create new robots under certain conditions, analogous to biological reproduction or replication:
    * Cloning: A simple form of reproduction (simple reproduction) – a robot might clone itself if certain criteria are met (sufficient energy, no nearby competition, etc.). The new robot (child) initially has the same "DNA" (properties and brain parameters) as the parent, possibly with slight random mutations (to introduce variation).
    * Combining Traits (combined reproduction): If two or more robots are strongly connected (and perhaps have compatible types), they can produce a offspring that mixes their features. For example, we take some properties from one parent and some from the other (this can be literal, like color or size averages, or more abstract like merging neural network weights or rules). This is inspired by genetic algorithms: by producing a child solution via crossover and mutation, the result shares many characteristics of its parents. We treat each robot's configuration as a "genome" – including things like its brain's parameters or high-level traits – which can be inherited and combined. In both cases it is about the ability to simulate the building of large dependent structures that, thanks to external energy, can grow, creating additional cells.

* **State Saving/Loading:** The World class provides methods to save the current state to a JSON file and to load from a file. This includes all necessary information to reconstruct the world: each object's type, position, properties (energy, color, etc.), and connections, as well as any time counters relevant (like how long connections have lasted if needed). This feature is crucial for long-running simulations and collaborative development (teams can share a world snapshot that reproduces an interesting scenario or bug). It also helps in training workflows – one could save the state of a simulation and resume training an RL agent from that point, or evaluate it later. The JSON format ensures the saved state is human-readable and easily version-controlled if placed in a repository.

---
## Configuration System

The framework now includes a unified JSON-based configuration system that allows both the Ursina engine and WebGL engine to use identical world and robot descriptions. This enables easy experimentation with different scenarios without modifying code.

### Quick Start

**Basic Usage:**
```bash
# Run with default configuration
python examples/run_demo.py
python examples/web_visualization/webserver_demo.py

# Run with custom configuration
python examples/run_with_config.py --config advanced_world_config.json
python examples/web_visualization/run_webgl_with_config.py --config ../advanced_world_config.json

# List available configurations
python examples/run_with_config.py --list-configs
```

### Configuration Files

- `examples/world_config.json` - Basic configuration matching original demo
- `examples/advanced_world_config.json` - Advanced configuration with various resource types and robot behaviors

### Configuration Format

```json
{
  "world": {
    "name": "Demo World",
    "description": "A simple demo world with robots and resources",
    "simulation": {
      "time_step": 0.1,
      "max_steps": 1000
    }
  },
  "static_elements": [
    {
      "position": [5, 0, 0],
      "color": [1, 0, 1],
      "resource_value": 40,
      "resource_type": "ENERGY",
      "decay_rate": 0.0,
      "respawn_time": null,
      "max_uses": null,
      "is_obstacle": false,
      "is_collectible": true
    }
  ],
  "robots": [
    {
      "position": [0, 0, 0],
      "color": [1, 0, 0],
      "brain_type": "RuleBasedBrain",
      "max_energy": 100.0,
      "movement_cost": 1.0,
      "reproduction_threshold": 20.0,
      "name": "Red Robot"
    }
  ]
}
```

For detailed configuration documentation, see `examples/README_CONFIG.md`.

---
## API Reference

### Core Classes

#### World
```python
from vbe_3d.core.world import World

world = World(engine)
world.add_robot(robot)
world.add_static(element)
world.step()  # Advance simulation
world.save_state("save.json")
world.load_state("save.json")
```

#### Robot
```python
from vbe_3d.core.robot import Robot
from vbe_3d.brain.rule_based import RuleBasedBrain

robot = Robot(
    position=(0, 0, 0),
    color=(1, 0, 0),
    brain=RuleBasedBrain(),
    max_energy=100.0
)
```

#### StaticElement
```python
from vbe_3d.core.static_element import StaticElement, ResourceType

element = StaticElement(
    position=(5, 0, 0),
    color=(1, 0, 1),
    resource_value=40,
    resource_type=ResourceType.ENERGY
)
```

### Brain Types

#### RuleBasedBrain
Simple rule-based behavior for robots.

#### RLBrain
Reinforcement learning brain using PyTorch neural networks.

---
## Examples

### Basic Usage

```python
from vbe_3d.engine.ursina_engine import UrsinaEngine
from vbe_3d.core.world import World
from vbe_3d.core.robot import Robot
from vbe_3d.core.static_element import StaticElement

# Initialize
engine = UrsinaEngine()
world = World(engine)

# Add elements
world.add_static(StaticElement(position=(5, 0, 0), color=(1, 0, 1)))
world.add_robot(Robot(position=(0, 0, 0), color=(1, 0, 0)))

# Run simulation
engine.run(world)
```

### Custom Robot Brain

```python
from vbe_3d.brain.base_brain import RobotBrain

class CustomBrain(RobotBrain):
    def decide_action(self, observation):
        # Custom decision logic
        return 1  # Move in +X direction
```

### Using Configuration

```python
from examples.config_loader import ConfigLoader

world = ConfigLoader.create_world_from_config(engine, "config.json")
```

---
## How to run:

Clone the repo and install dependencies from requirements.txt.
    
```
pip install -r requirements.txt
```

### Basic Examples

Run the default demo:
```
python ./examples/run_demo.py
```

Run with custom configuration:
```
python ./examples/run_with_config.py --config advanced_world_config.json
```

In case of problems you can check if the 3D environment starts correctly using this example:

```
python ./examples/camera_minimal_test.py
```

### WebGL Examples

Run the WebGL demo:
```
python ./examples/web_visualization/webserver_demo.py
```

Run WebGL with custom configuration:
```
python ./examples/web_visualization/run_webgl_with_config.py --config ../advanced_world_config.json
```

---
## Camera Controls

* Right mouse button + keys QWEASD: Move/Pan camera
* Middle mouse button + drag: Rotate camera
* Mouse wheel: Zoom in/out
* WASD: Move camera
* QE: Move camera up/down

---
## Debug Mode

```python
engine = UrsinaEngine(debug=True)  # Enable debug logging
```

---
## Roadmap:

* [X] Camera controls for better user interaction.
* [X] Unified JSON configuration system for both engines.
* [X] WebGL renderer (Three.js) for browser demos.
* [ ] Physics integration (Panda3D Bullet or PyBullet).
* [ ] Multi‑agent RL via PettingZoo API.
* [ ] Visual debugging HUD (energy bars, connection graph).
* [ ] Full evolutionary training pipeline.
* [ ] Ability to control each robot via a dedicated API Endpoint.

---
## License:

Virtual Bot Enviroment 3D is released under the **MIT License** — see [`LICENSE`](https://github.com/rsobieski/Virtual-Bot-Environment-3D/blob/main/LICENSE) for details.

