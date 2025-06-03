import random
from typing import List

from .base_brain import RobotBrain


class RuleBasedBrain(RobotBrain):
    """A simple hard-coded logic for the robot."""
    def __init__(self):
        super().__init__()
        # we could add parameters for the behavior, but for now it's static rules.

    def decide_action(self, observation):
        # observation as defined in Robot.perceive: [res_dx, res_dy, res_dz, bot_dx, bot_dy, bot_dz, energy_norm]
        # simple strategy:
        # if a resource is very close (within 1 unit), move towards it.
        res_dx, res_dy, res_dz = observation[0], observation[1], observation[2]
        # if resource is nearby in any direction significantly, head that way:
        if abs(res_dx) > 0.1 or abs(res_dz) > 0.1 or abs(res_dy) > 0.1:
            # move in direction of resource (choose the axis with largest distance)
            if abs(res_dx) >= max(abs(res_dy), abs(res_dz)):
                return 1 if res_dx > 0 else 2  # move +x if resource is positive dx away, else -x
            elif abs(res_dz) >= max(abs(res_dx), abs(res_dy)):
                return 3 if res_dz > 0 else 4  # move in z towards resource
            elif abs(res_dy) >= max(abs(res_dx), abs(res_dz)):
                return 5 if res_dy > 0 else 6  # move in y (vertical) towards resource
        # otherwise, if no immediate resource target, do a random walk (or stay put if energy low)
        if self.robot and self.robot.energy < 10:
            return 0  # if energy is very low, do nothing to conserve (as a simple rule)
        return random.choice([0,1,2,3,4])  # randomly move (not using vertical in random to keep on ground for simplicity)
