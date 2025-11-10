# backend/env_wrapper.py
from envs.cbs_wrapper import CBSWrapper

class ScenarioEnv:
    def __init__(self, scenario=None):
        # scenario currently ignored because we use maritime preset
        print("[env_wrapper] Creating CBSWrapper with CyberBattleTiny-v0")
        self.cbs = CBSWrapper("CyberBattleTiny-v0")


    @classmethod
    def from_json(cls, scenario):
        # keep signature compatible with previous code; you can parse scenario later
        return cls(scenario)

    def reset(self):
        return self.cbs.reset()

    def step(self, action):
        # action must be a CyberBattleSim-formatted action dict
        return self.cbs.step(action)

    def render_state(self):
        # return nodes ready to emit to frontend
        return self.cbs.get_node_list()
