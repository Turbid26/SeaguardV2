# backend/agents/mappo.py
import os
import threading
from typing import Dict, Any
import numpy as np

# import the dynamic adapter
from adapters.load_mappo_dynamic import MAPPOforCBS

# Ensure thread-safety for model lazy-load (simulate runs in a Thread)
_model_lock = threading.Lock()
_model_singleton = None

def _get_mappo_model():
    """
    Lazy-load a single global MAPPOforCBS instance.
    Use path relative to backend CWD (seaguard/backend).
    """
    global _model_singleton
    if _model_singleton is not None:
        return _model_singleton

    with _model_lock:
        if _model_singleton is not None:
            return _model_singleton

        # model location (CWD is seaguard/backend in your setup)
        # adjust if you store model elsewhere
        ckpt_rel = os.path.join("models", "final-torch.model")
        if not os.path.exists(ckpt_rel):
            raise FileNotFoundError(f"MAPPO checkpoint not found at: {ckpt_rel}")

        print("[mappo.agent] Loading MAPPO model from:", ckpt_rel)
        _model_singleton = MAPPOforCBS(ckpt_rel, num_agents=8)
        # ensure RNN states are fresh
        _model_singleton.reset_hidden_states()
        return _model_singleton

class MAPPOAgentWrapper:
    """
    Thin wrapper providing the single-agent act(obs) API expected by simulate().
    Internally calls the multi-agent adapter and returns a single action dict.
    """
    def __init__(self):
        # don't call loader here in constructor to keep startup light — lazy load in act()
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            self._model = _get_mappo_model()

    def reset(self):
        """Reset RNN hidden states (call after env.reset())."""
        self._ensure_model()
        self._model.reset_hidden_states()

    def act(self, raw_obs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Single-action API: given the latest raw CBS observation dict, return an action dict.
        Strategy:
          - create a synthetic obs_list of length num_agents by duplicating raw_obs
          - call adapter.act_for_agents(...) and return the first agent's action
        """
        self._ensure_model()

        # build list of per-agent observations (duplicate for demo). You can replace this
        # with per-node observations when you map CBS hosts -> agents.
        obs_list = [raw_obs for _ in range(self._model.num_agents)]

        # get full-agent actions from loaded MAPPO
        actions = self._model.act_for_agents(obs_list)

        # choose primary agent's action to execute in CBS (simple for demo)
        primary_action = actions[0] if actions else {"noop": 0}
        return primary_action

# convenience - instantiate a module-level object that other code can import
# e.g.: from backend.agents.mappo import MAPPO_AGENT ; action = MAPPO_AGENT.act(obs)
MAPPO_AGENT = MAPPOAgentWrapper()
