# Configuration System

This directory now contains a unified configuration system that allows both the Ursina engine (`run_demo.py`) and WebGL engine (`webserver_demo.py`) to use the same world and robot descriptions from JSON configuration files.

## Configuration Files

### Basic Configuration (`world_config.json`)
A simple configuration with two robots and two static elements, matching the original demo setup.

### Advanced Configuration (`advanced_world_config.json`)
A more complex configuration demonstrating:
- Different resource types (ENERGY, MATERIAL)
- Obstacles (non-collectible elements)
- Robots with different brain types and parameters
- Resources with decay and respawn mechanics

## Configuration Format

### World Settings
```json
{
  "world": {
    "name": "Demo World",
    "description": "A simple demo world with robots and resources",
    "simulation": {
      "time_step": 0.1,
      "max_steps": 1000
    }
  }
}
```

### Static Elements
```json
{
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
  ]
}
```

### Robots
```json
{
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

## Usage

### Running with Default Configuration

**Ursina Engine:**
```bash
python run_demo.py
```

**WebGL Engine:**
```bash
python web_visualization/webserver_demo.py
```

### Running with Custom Configuration

**Ursina Engine:**
```bash
python run_with_config.py --config advanced_world_config.json
```

**WebGL Engine:**
```bash
python web_visualization/run_webgl_with_config.py --config ../advanced_world_config.json
```

### Listing Available Configurations
```bash
python run_with_config.py --list-configs
python web_visualization/run_webgl_with_config.py --list-configs
```

## Configuration Parameters

### Static Elements
- `position`: [x, y, z] coordinates
- `color`: [r, g, b] color values (0.0 to 1.0)
- `resource_value`: Amount of energy/resources provided
- `resource_type`: Type of resource ("ENERGY", "MATERIAL", "SPECIAL")
- `decay_rate`: Rate at which resource value decreases over time
- `respawn_time`: Time steps before resource respawns (null for no respawn)
- `max_uses`: Maximum times resource can be collected (null for unlimited)
- `is_obstacle`: Whether the element blocks robot movement
- `is_collectible`: Whether robots can collect this resource

### Robots
- `position`: [x, y, z] starting coordinates
- `color`: [r, g, b] robot color
- `brain_type`: Type of brain ("RuleBasedBrain", "RLBrain")
- `max_energy`: Maximum energy capacity
- `movement_cost`: Energy cost per movement step
- `reproduction_threshold`: Minimum energy required for reproduction
- `name`: Optional name for the robot

## Benefits

1. **Unified Configuration**: Both engines now use the same configuration format
2. **Easy Experimentation**: Quickly test different world setups without code changes
3. **Reproducible Experiments**: Save and share exact world configurations
4. **Flexible Parameters**: Easy to adjust robot behaviors and world properties
5. **Extensible**: Easy to add new configuration parameters

## Creating Custom Configurations

1. Copy an existing configuration file
2. Modify the parameters as needed
3. Save with a descriptive name (e.g., `my_experiment_config.json`)
4. Run with the new configuration using the `--config` parameter

## Example Custom Configuration

```json
{
  "world": {
    "name": "My Experiment",
    "description": "Testing robot cooperation with limited resources",
    "simulation": {
      "time_step": 0.05,
      "max_steps": 5000
    }
  },
  "static_elements": [
    {
      "position": [10, 0, 0],
      "color": [0, 1, 0],
      "resource_value": 100,
      "resource_type": "ENERGY",
      "decay_rate": 0.5,
      "respawn_time": 200,
      "max_uses": 5,
      "is_obstacle": false,
      "is_collectible": true
    }
  ],
  "robots": [
    {
      "position": [0, 0, 0],
      "color": [1, 0, 0],
      "brain_type": "RLBrain",
      "max_energy": 150.0,
      "movement_cost": 0.5,
      "reproduction_threshold": 30.0,
      "name": "Fast Learner"
    }
  ]
}
``` 