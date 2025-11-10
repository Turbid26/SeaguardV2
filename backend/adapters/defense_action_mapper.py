# backend/adapters/defense_action_mapper.py
import numpy as np
from typing import Dict

MARITIME_ORDER = [
  "HMI_Bridge",
  "PLC_Engine",
  "PLC_Ballast",
  "SCADA_Server",
  "Radar_System",
  "Navigation_Server",
  "Firewall",
  "Switch_Core",
]

def logits_to_defense_action(logits: np.ndarray) -> Dict:
    idx = int(np.argmax(logits))
    if idx < 8:
        node = MARITIME_ORDER[idx]
        defense = "patch"
    else:
        node = MARITIME_ORDER[idx - 8]
        defense = "isolate"
    return {"node": node, "defense": defense}
