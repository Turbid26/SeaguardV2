# backend/adapters/cbs_obs_adapter.py
import numpy as np
from typing import Dict, Any

TARGET_DIM = 162

def obs_to_162_vector(raw_obs: Dict[str, Any]) -> np.ndarray:
    features = []
    # basic numeric flags
    features.append(float(raw_obs.get("newly_discovered_nodes_count", 0)))
    features.append(float(raw_obs.get("lateral_move", 0)))
    features.append(float(raw_obs.get("customer_data_found", 0)))
    features.append(float(raw_obs.get("escalation", 0)))
    # leaked credentials summary
    leaked = raw_obs.get("leaked_credentials", None)
    if leaked is None:
        features.append(0.0)
    else:
        try:
            s = sum(int(np.sum(np.array(x))) for x in leaked)
            features.append(float(s))
        except Exception:
            try:
                features.append(float(np.sum(np.array(leaked))))
            except Exception:
                features.append(0.0)
    # action mask summaries
    am = raw_obs.get("action_mask", {}) or {}
    for k in ("local_vulnerability", "remote_vulnerability", "connect", "lateral_move"):
        arr = am.get(k)
        try:
            a = np.array(arr)
            features.append(float(a.size))
            features.append(float((a == 1).sum()))
            features.append(float(a.shape[0] if a.ndim >= 1 else 0.0))
        except Exception:
            features.extend([0.0, 0.0, 0.0])
    # discovered nodes / privilege stats
    try:
        dcount = raw_obs.get("discovered_node_count", None)
        if dcount is None:
            dn = raw_obs.get("_discovered_nodes", None)
            if isinstance(dn, (list, tuple, np.ndarray)):
                features.append(float(len(dn)))
            else:
                features.append(0.0)
        else:
            features.append(float(dcount))
    except Exception:
        features.append(0.0)
    try:
        nodes_priv = raw_obs.get("nodes_privilegelevel", None)
        if nodes_priv is not None:
            arr = np.array(nodes_priv, dtype=float)
            features.append(float(np.nanmean(arr)))
            features.append(float(np.nanmax(arr)))
            features.append(float(np.nanmin(arr)))
        else:
            features.extend([0.0, 0.0, 0.0])
    except Exception:
        features.extend([0.0, 0.0, 0.0])
    # probe result sum
    pr = raw_obs.get("probe_result", None)
    try:
        features.append(float(np.sum(np.array(pr))) if pr is not None else 0.0)
    except Exception:
        features.append(0.0)
    # pad to TARGET_DIM
    vec = np.array(features, dtype=np.float32)
    if vec.size >= TARGET_DIM:
        return vec[:TARGET_DIM]
    pad = np.zeros(TARGET_DIM - vec.size, dtype=np.float32)
    return np.concatenate([vec, pad])
