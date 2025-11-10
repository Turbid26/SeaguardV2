from cyberbattle.simulation.env import CyberBattleEnv
from cyberbattle.simulation import model
from cyberbattle.datasets.toy.corporate import tiny_corporate

class CBSWrapper:
    """
    Wraps CyberBattleSim into a simple Gym-like API for SeaGuard use
    """
    def __init__(self):
        self.env = CyberBattleEnv(
            network=tiny_corporate,
            vulnerability_library=None,
            sample_random_lookups=True
        )
        self.obs = None

    def reset(self):
        self.obs = self.env.reset()
        return self._format_obs(self.obs)

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.obs = obs
        return self._format_obs(obs), reward, done, info

    def _format_obs(self, obs):
        """
        Convert CBS observation into node-state list for your UI
        """
        node_states = []
        for node_id, node in obs.attacker.nodes.items():
            compromised = node.properties.get("Compromised", False)
            node_states.append({
                "id": node_id,
                "status": "compromised" if compromised else "safe",
                "vulns": list(node.properties.get("vulnerabilities", []))
            })
        return node_states
