from .rule_based import RuleBasedBrain
from .rl_brain import RLBrain


def brain_from_export(data: dict):
    t = data["type"]
    if t == "RLBrain":
        return RLBrain()
    return RuleBasedBrain()
