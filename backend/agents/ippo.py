import numpy as np
import random

class IPPOAgent:
    """
    Aggressive agent:
    - Prioritizes exploiting any vulnerability it sees
    - Then tries credential abuse or lateral movement
    - Basically tries to push action fast
    """

    def act(self, obs):
        mask = obs.get("action_mask", {})

        # 1) Always exploit local vulnerabilities first (aggressive attack mindset)
        lv = mask.get("local_vulnerability")
        if lv is not None:
            lv = np.array(lv)
            if np.any(lv == 1):
                r, c = np.argwhere(lv == 1)[0]
                return {"local_vulnerability": (int(r), int(c))}

        # 2) Next try credentials
        cred = mask.get("credential_use")
        if cred is not None:
            cred = np.array(cred)
            if np.any(cred == 1):
                r, c = np.argwhere(cred == 1)[0]
                return {"credential_use": (int(r), int(c))}

        # 3) Try lateral movement if exploitation not possible
        lm = mask.get("lateral_move")
        if lm is not None:
            lm = np.array(lm)
            if np.any(lm == 1):
                r, c = np.argwhere(lm == 1)[0]
                return {"lateral_move": (int(r), int(c))}

        # 4) No valid actions → noop
        return {"noop": 0}
