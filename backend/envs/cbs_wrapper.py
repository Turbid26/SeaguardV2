# backend/envs/cbs_wrapper.py
import gymnasium as gym
import cyberbattle        # ensures package code is loaded
import cyberbattle._env   # registers the envs
import numpy as np
import logging
from typing import List, Dict, Any
from datetime import datetime

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -------- MITRE ATT&CK Tagging ---------
MITRE_MAP = {
    "discovered_node": [{"id": "T1595", "name": "Active Scanning"}],
    "exploit": [{"id": "T1190", "name": "Exploit Public-Facing Application"}],
    "leaked_credentials": [{"id": "T1555", "name": "Credentials from Password Stores"}],
    "lateral_move": [{"id": "T1021", "name": "Remote Services (Lateral Movement)"}],
    "escalation": [{"id": "T1068", "name": "Privilege Escalation"}],
    "credential_use": [{"id": "T1550", "name": "Use of Valid Accounts"}],
    "impact": [{"id": "T1486", "name": "Data Encrypted for Impact"}]
}

def now_iso():
    return datetime.utcnow().isoformat() + "Z"
# ------------------------------------------------------------------

# Maritime preset node list (human-friendly names)
MARITIME_NODES = [
    "HMI_Bridge",
    "PLC_Engine",
    "PLC_Ballast",
    "SCADA_Server",
    "Radar_System",
    "Navigation_Server",
    "Firewall",
    "Switch_Core"
]

class CBSWrapper:
    """
    Wraps a CyberBattleSim gym env into a simple interface returning
    a list of maritime nodes with statuses and properties consumable by frontend.
    Includes MITRE tagging and a deterministic mapping from CBS host index -> maritime node name.
    """

    def __init__(self, env_id: str = "CyberBattleTiny-v0"):
        # Force the desired env (Tiny best for maritime demo, Chain for linear demos)
        self.requested_env = env_id or "CyberBattleTiny-v0"
        print(f"[CBSWrapper] FORCING env -> {self.requested_env}")

        # instantiate env class directly (bypass any registry aliasing)
        if "Tiny" in self.requested_env:
            try:
                from cyberbattle._env.cyberbattle_tiny import CyberBattleTiny
                self.env = CyberBattleTiny()
            except Exception:
                # fallback to gym.make if direct class not found
                self.env = gym.make(self.requested_env)
        elif "Chain" in self.requested_env:
            try:
                from cyberbattle._env.cyberbattle_chain import CyberBattleChain
                self.env = CyberBattleChain()
            except Exception:
                self.env = gym.make(self.requested_env)
        else:
            self.env = gym.make(self.requested_env)

        # For safety wrap with OrderEnforcing if available
        try:
            from gymnasium.wrappers import OrderEnforcing
            if not isinstance(self.env, OrderEnforcing):
                self.env = OrderEnforcing(self.env)
        except Exception:
            pass

        self.env_id = self.requested_env
        self.obs = None
        self.info = None

        # Track internal status for maritime nodes
        self.node_status = {n: "safe" for n in MARITIME_NODES}
        self.node_counters = {n: {"compromised_count": 0} for n in MARITIME_NODES}
        self._last_events: List[Dict[str, Any]] = []

        # mapping from cbs host index -> maritime node name
        self.cbs_to_maritime: Dict[int, str] = {}
        self._inferred_host_count: int | None = None

    # ------------------ mapping helpers ------------------
    def _ensure_index_mapping(self):
        if self._inferred_host_count is not None and self.cbs_to_maritime:
            return
        try:
            obs = self.obs or {}
            mask = obs.get("action_mask", {}) if isinstance(obs, dict) else {}
            lv = mask.get("local_vulnerability") if isinstance(mask, dict) else None
            if lv is not None:
                arr = np.array(lv)
                host_count = arr.shape[0]
            else:
                rv = mask.get("remote_vulnerability") if isinstance(mask, dict) else None
                if rv is not None:
                    host_count = np.array(rv).shape[0]
                else:
                    host_count = len(MARITIME_NODES)
        except Exception:
            host_count = len(MARITIME_NODES)

        self._inferred_host_count = int(host_count)
        for i in range(self._inferred_host_count):
            self.cbs_to_maritime[i] = MARITIME_NODES[i % len(MARITIME_NODES)]
        print(f"[CBSWrapper] Inferred host_count={self._inferred_host_count}; mapping created.")

    def _map_mask_idx_to_node(self, idx_row: int) -> str:
        self._ensure_index_mapping()
        return self.cbs_to_maritime.get(int(idx_row), MARITIME_NODES[int(idx_row) % len(MARITIME_NODES)])

    # ------------------ MITRE event helpers ------------------
    def _emit(self, node: str, etype: str, description: str = ""):
        ev = {
            "time": now_iso(),
            "node": node,
            "type": etype,
            "description": description,
            "mitre": MITRE_MAP.get(etype, [])
        }
        self._last_events.append(ev)
        if len(self._last_events) > 40:
            self._last_events = self._last_events[-40:]

    def _get_events(self) -> List[Dict[str, Any]]:
        e = self._last_events.copy()
        self._last_events.clear()
        return e

    # ------------------ main API ------------------
    def reset(self) -> List[Dict[str, Any]]:
        obs, info = self.env.reset()
        self.obs = obs
        self.info = info

        # reset node trackers
        for n in MARITIME_NODES:
            self.node_status[n] = "safe"
            self.node_counters[n] = {"compromised_count": 0}

        # ensure mapping can be created from initial obs
        self._ensure_index_mapping()

        # derive initial statuses (heuristic)
        self._update_node_status_from_obs(obs, None)
        return self.get_node_list()

    def step(self, action: Dict[str, Any]):
        # pass action directly to gym env
        out = self.env.step(action)
        # gym may return (obs, reward, terminated, truncated, info)
        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            done = bool(terminated or truncated)
        else:
            obs, reward, done, info = out

        self.obs = obs
        self.info = info

        # ensure mapping (in case reset didn't expose mask)
        self._ensure_index_mapping()

        # update maritime node mapping heuristics
        self._update_node_status_from_obs(obs, action)

        return self.get_node_list(), float(reward), bool(done), {"events": self._get_events()}

    # ------------------ observation -> maritime mapping ------------------
    def _update_node_status_from_obs(self, obs: Dict[str, Any], action: Dict[str, Any] | None = None):
        # safe guards
        if not isinstance(obs, dict):
            return

        # map leaked credentials -> compromised server(s)
        leaked = obs.get("leaked_credentials", None)
        if leaked is not None:
            try:
                total_leaks = sum(int(np.sum(a)) for a in leaked if hasattr(a, "shape"))
            except Exception:
                total_leaks = 0
            if total_leaks > 0:
                # pick a maritime node mapped from first discovered index if available
                discovered = obs.get("discovered_nodes_properties", None)
                if isinstance(discovered, (list, tuple)) and len(discovered) > 0:
                    chosen_node = self._map_mask_idx_to_node(0)
                else:
                    chosen_node = "SCADA_Server"
                self.node_status[chosen_node] = "compromised"
                self.node_counters[chosen_node]["compromised_count"] += int(total_leaks)
                self._emit(chosen_node, "leaked_credentials", "Credential dump observed")

        # lateral movement signal -> mark target node as under attack or compromised
        lateral = obs.get("lateral_move", 0)
        if lateral and int(lateral) > 0:
            # prefer to use action_mask if present to find row
            mask = obs.get("action_mask", {}) if isinstance(obs, dict) else {}
            lv = mask.get("local_vulnerability") if isinstance(mask, dict) else None
            lm = mask.get("lateral_move") if isinstance(mask, dict) else None

            target_idx = None
            if lm is not None:
                arr = np.array(lm)
                idxs = np.argwhere(arr == 1)
                if idxs.size:
                    target_idx = int(idxs[0][0])
            elif lv is not None:
                arr = np.array(lv)
                idxs = np.argwhere(arr == 1)
                if idxs.size:
                    target_idx = int(idxs[0][0])

            if target_idx is None:
                # fallback: map lateral scalar to a node index
                try:
                    target_idx = int(lateral) % (self._inferred_host_count or len(MARITIME_NODES))
                except Exception:
                    target_idx = 0

            chosen = self._map_mask_idx_to_node(target_idx)
            # if already under attack, escalate to compromised
            if self.node_status.get(chosen, "safe") == "safe":
                self.node_status[chosen] = "under_attack"
            else:
                self.node_status[chosen] = "compromised"
            if self.node_status[chosen] == "compromised":
                self.node_counters[chosen]["compromised_count"] += 1
            self._emit(chosen, "lateral_move", "Lateral movement detected")

        # escalation -> convert highest attacked node to compromised
        esc = obs.get("escalation", 0)
        if esc and int(esc) > 0:
            # pick the node with highest compromised_count
            most = max(self.node_counters.items(), key=lambda x: x[1].get("compromised_count", 0))[0]
            self.node_status[most] = "compromised"
            self._emit(most, "escalation", "Privilege escalation observed")

        # action_mask presence -> mark nodes under attack if they are actionable
        mask = obs.get("action_mask", {}) if isinstance(obs, dict) else {}
        if isinstance(mask, dict):
            for key in ("local_vulnerability", "lateral_move"):
                arr = mask.get(key, None)
                if arr is None:
                    continue
                arr = np.array(arr)
                if arr.size:
                    idxs = np.argwhere(arr == 1)
                    if idxs.size:
                        r = int(idxs[0][0])
                        chosen = self._map_mask_idx_to_node(r)
                        if self.node_status.get(chosen, "safe") == "safe":
                            self.node_status[chosen] = "under_attack"
                            self._emit(chosen, "discovered_node", f"Action available: {key}")

    # ------------------ UI output ------------------
    def get_node_list(self) -> List[Dict[str, Any]]:
        nodes = []
        for n in MARITIME_NODES:
            properties = {
                "vuln_score": float(self._vuln_score_for(n)),
                "alert_prob": 0.05 + 0.05 * (self.node_counters[n]["compromised_count"])
            }
            nodes.append({
                "id": n,
                "status": self.node_status[n],
                "properties": properties
            })
        return nodes

    def _vuln_score_for(self, node_name: str) -> float:
        if "Server" in node_name or "HMI" in node_name or "PLC" in node_name:
            base = 0.6
        elif "Firewall" in node_name:
            base = 0.2
        else:
            base = 0.3
        mod = self.node_counters[node_name].get("vuln_modifier", 1.0)
        return float(max(0.0, min(1.0, base * mod)))

    
    def apply_defense(self, node_name: str, defense: str) -> bool:
        """
        Apply a defender action to a maritime node: 'patch' or 'isolate'
        """
        if node_name not in self.node_status:
            return False

        if defense == "patch":
            prev = self.node_counters[node_name].get("patched_count", 0)
            self.node_counters[node_name]["patched_count"] = prev + 1
            self.node_counters[node_name]["vuln_modifier"] = max(
                0.0, self.node_counters[node_name].get("vuln_modifier", 1.0) * 0.75
            )
            # increase alert probability a bit
            self.node_counters[node_name]["alert_boost"] = self.node_counters[node_name].get("alert_boost", 0.0) + 0.05
            self._emit(node_name, "defense_patch", "Applied patch/hardening")
            return True

        if defense == "isolate":
            self.node_status[node_name] = "safe"
            self.node_counters[node_name]["isolated"] = True
            self._emit(node_name, "defense_isolate", "Node isolated from network")
            return True

        return False


    def _emit_edge_event(self, src_node: str | None, dst_node: str, etype: str, description: str = ""):
        """
        Emit an event that includes an edge (source -> target). src_node may be None if unknown.
        """
        ev = {
            "time": now_iso(),
            "node": dst_node,
            "type": etype,
            "description": description,
            "mitre": MITRE_MAP.get(etype, []),
            "edge": {"from": src_node, "to": dst_node}  # useful for path visualization
        }
        self._last_events.append(ev)
        if len(self._last_events) > 40:
            self._last_events = self._last_events[-40:]

