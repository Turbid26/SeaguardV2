# backend/adapters/load_mappo_dynamic.py
import os
import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Any, Tuple

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------- Infer shapes helpers ----------
def infer_mlp_shapes(state_dict: Dict[str, torch.Tensor]) -> List[Tuple[int,int]]:
    mlp_shapes = []
    for k, v in state_dict.items():
        if "mlp" in k and k.endswith(".weight"):
            if len(v.shape) == 2:
                out_f, in_f = v.shape
                mlp_shapes.append((int(in_f), int(out_f)))
            else:
                # skip 1D weights (bias / norm)
                # print(f"[skip] non-2D mlp weight {k} shape {v.shape}")
                pass
    if not mlp_shapes:
        # fallback: try to find some linear-like weights
        for k,v in state_dict.items():
            if "weight" in k and len(v.shape)==2:
                out_f, in_f = v.shape
                mlp_shapes.append((int(in_f), int(out_f)))
                break
    if not mlp_shapes:
        raise RuntimeError("No MLP weight matrices found in actor_state_dict")
    return mlp_shapes

def infer_gru_input_and_hidden(state_dict: Dict[str, torch.Tensor]) -> Tuple[int,int]:
    # find weight_ih_l0 (shape: 3*hidden, input_size)
    key = None
    for cand in ("rnn.gru.weight_ih_l0", "rnn.gru.weight_ih", "rnn.weight_ih_l0"):
        if cand in state_dict:
            key = cand
            break
    if key is None:
        # scan for any key containing weight_ih
        for k in state_dict.keys():
            if "gru" in k and "weight_ih" in k:
                key = k
                break
    if key is None:
        raise RuntimeError("GRU weight_ih key not found in actor_state_dict.")
    w = state_dict[key]
    rows, cols = w.shape
    hidden = rows // 3
    input_size = cols
    return int(input_size), int(hidden)

def infer_output_dim(state_dict: Dict[str, torch.Tensor]) -> int:
    for k in state_dict.keys():
        if k.endswith("output.weight") or k.endswith("output_layer.weight") or "output.weight" in k:
            return int(state_dict[k].shape[0])
    # fallback: any weight with small out_dim <= 256 that looks like final
    candidate = None
    for k,v in state_dict.items():
        if "weight" in k and len(v.shape)==2:
            out_f, in_f = v.shape
            if out_f <= 256:
                candidate = out_f
                break
    if candidate is not None:
        return int(candidate)
    raise RuntimeError("Could not infer output/action dim.")

# ---------- Dynamic actor builder ----------
class DynamicMAPPOActor(nn.Module):
    def __init__(self, mlp_shapes: List[Tuple[int,int]], gru_input: int, gru_hidden: int, action_dim: int):
        super().__init__()
        obs_dim = mlp_shapes[0][0] if mlp_shapes else gru_input
        self.feature_norm = nn.LayerNorm(obs_dim)

        # Build MLP as sequence of Linear + ReLU to match mlp.<i> pairs
        layers = []
        for (in_f, out_f) in mlp_shapes:
            layers.append(nn.Linear(in_f, out_f))
            layers.append(nn.ReLU())
        self.mlp = nn.Sequential(*layers) if layers else nn.Identity()

        self.gru = nn.GRU(input_size=mlp_shapes[-1][1] if mlp_shapes else gru_input,
                          hidden_size=gru_hidden,
                          batch_first=True)
        self.gru_layer_norm = nn.LayerNorm(gru_hidden)
        self.output = nn.Linear(gru_hidden, action_dim)

    def forward(self, x: torch.Tensor, hidden: torch.Tensor = None):
        # x: (batch, seq_len, obs_dim)
        b, t, d = x.shape
        x = self.feature_norm(x.view(-1, d)).view(b, t, d)
        # flatten time axis to apply mlp
        out = x.view(b * t, -1)
        out = self.mlp(out)
        out = out.view(b, t, -1)
        out, h = self.gru(out, hidden)
        out = self.gru_layer_norm(out)
        logits = self.output(out)
        return logits, h

# ---------- Build actor from state dict ----------
def build_actor_from_actor_state_dict(actor_sd: Dict[str, torch.Tensor]) -> Tuple[DynamicMAPPOActor, Dict[str, Any]]:
    mlp_shapes = infer_mlp_shapes(actor_sd)
    gru_input, gru_hidden = infer_gru_input_and_hidden(actor_sd)
    action_dim = infer_output_dim(actor_sd)
    actor = DynamicMAPPOActor(mlp_shapes, gru_input, gru_hidden, action_dim)
    meta = {"mlp_shapes": mlp_shapes, "gru_input": gru_input, "gru_hidden": gru_hidden, "action_dim": action_dim}
    return actor, meta

def load_actor_from_checkpoint(path: str) -> Tuple[DynamicMAPPOActor, Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    ckpt = torch.load(path, map_location="cpu")
    if isinstance(ckpt, dict) and "actor_state_dict" in ckpt:
        actor_sd = ckpt["actor_state_dict"]
    elif isinstance(ckpt, dict) and "state_dict" in ckpt:
        actor_sd = ckpt["state_dict"]
    elif isinstance(ckpt, dict):
        # maybe it's a bare state_dict
        actor_sd = ckpt
    else:
        raise RuntimeError("Unsupported checkpoint format")
    actor, meta = build_actor_from_actor_state_dict(actor_sd)
    # load matching keys permissively
    model_state = actor.state_dict()
    loaded = {}
    for k, v in actor_sd.items():
        kk = k
        # try stripping common prefixes
        for p in ("module.", "actor.", "model.", "policy."):
            if kk.startswith(p):
                kk2 = kk[len(p):]
            else:
                kk2 = kk
            if kk2 in model_state and model_state[kk2].shape == v.shape:
                loaded[kk2] = v
                break
    model_state.update(loaded)
    actor.load_state_dict(model_state)
    actor.to(DEVICE)
    actor.eval()
    return actor, meta

# ---------- Adapter wrapper ----------
class MAPPOforCBS:
    def __init__(self, ckpt_path: str, num_agents: int = 8):
        assert os.path.exists(ckpt_path), f"checkpoint not found: {ckpt_path}"
        print("[MAPPOforCBS] Loading actor from:", ckpt_path)
        self.actor, self.meta = load_actor_from_checkpoint(ckpt_path)
        print("[MAPPOforCBS] meta:", self.meta)
        self.num_agents = num_agents
        self.hidden_states = [None] * self.num_agents
        # obs_dim inferred
        try:
            self.obs_dim = int(self.meta["mlp_shapes"][0][0])
        except Exception:
            self.obs_dim = int(self.meta.get("gru_input", 64))
        self.action_dim = int(self.meta["action_dim"])

    def reset_hidden_states(self):
        self.hidden_states = [None] * self.num_agents

    def act_for_agents(self, raw_obs_list: List[Dict[str, Any]]) -> List[np.ndarray]:
        # produce logits array per agent (not yet mapped to CBS)
        use = min(self.num_agents, len(raw_obs_list))
        vecs = []
        for i in range(use):
            vec = _obs_to_vector(raw_obs_list[i], size_hint=self.obs_dim)
            vecs.append(vec)
        if not vecs:
            return [{"noop": 0}] * self.num_agents
        x = np.stack(vecs, axis=0).astype(np.float32)
        x_t = torch.tensor(x, dtype=torch.float32, device=DEVICE).unsqueeze(1)  # (batch, seq=1, dim)
        # hidden assembly
        h_in = None
        if any(h is not None for h in self.hidden_states[:use]):
            hs = []
            for i in range(use):
                if self.hidden_states[i] is None:
                    hs.append(torch.zeros(1, 1, self.meta["gru_hidden"], device=DEVICE))
                else:
                    hs.append(self.hidden_states[i].to(DEVICE))
            h_in = torch.cat(hs, dim=1)  # (num_layers, batch, hidden)
        with torch.no_grad():
            logits_t, h_out = self.actor(x_t, hidden=h_in)
            logits = logits_t.squeeze(1).cpu().numpy()  # (batch, action_dim)
            if h_out is not None:
                for i in range(use):
                    self.hidden_states[i] = h_out[:, i:i+1, :].cpu()
        # return logits per agent as numpy arrays
        result = []
        for i in range(use):
            result.append(logits[i])
        # pad
        for _ in range(self.num_agents - use):
            result.append(np.zeros(self.action_dim, dtype=np.float32))
        return result

# ---------- small helper local obs->vec (simple duplicate of cbs_obs_adapter logic) ----------
def _obs_to_vector(raw_obs: Dict[str, Any], size_hint: int = None) -> np.ndarray:
    from adapters.cbs_obs_adapter import obs_to_162_vector
    v = obs_to_162_vector(raw_obs)
    if size_hint is None:
        return v
    if v.size >= size_hint:
        return v[:size_hint]
    pad = np.zeros(size_hint - v.size, dtype=np.float32)
    return np.concatenate([v, pad])
