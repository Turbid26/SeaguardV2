# backend/inspect_model.py
import torch
import os
from pprint import pprint

path = "./models/final-torch.model"  # <- adjust filename if needed

print("FILE:", path, "exists?", os.path.exists(path))
if not os.path.exists(path):
    raise SystemExit("model file not found at: " + path)

try:
    obj = torch.load(path, map_location="cpu")
except Exception as e:
    print("torch.load failed:", e)
    raise

print("Loaded type:", type(obj))

# Case A: full nn.Module saved (torch.save(model))
if hasattr(obj, "__class__") and hasattr(obj, "state_dict"):
    print("Looks like a full model object (nn.Module). Class:", obj.__class__)
    # safe: print top-level attr names
    print("Attributes on object:", [k for k in dir(obj) if not k.startswith("_")][:50])
    try:
        sd = obj.state_dict()
        print("state_dict keys (sample):", list(sd.keys())[:20])
    except Exception as e:
        print("Could not read state_dict:", e)
    # test forward with a dummy input if it accepts tensor input
    try:
        import torch
        # attempt a vector input
        dummy = torch.randn(1, 64)
        out = obj(dummy)
        print("Forward ran OK. Output shape:", getattr(out, "shape", type(out)))
    except Exception as e:
        print("Forward failed with dummy input:", e)

# Case B: dict - probably a state_dict or training checkpoint
elif isinstance(obj, dict):
    print("Loaded a dict. Keys:")
    pprint(list(obj.keys()))
    # Often keys: actor_state_dict, critic_state_dict, model_state_dict, state_dict, epoch, ...
    # Show nested key sample if state_dict present
    candidates = ["state_dict", "model_state_dict", "actor_state_dict", "policy_state_dict"]
    for c in candidates:
        if c in obj:
            print(f"Found candidate key: {c}. sample entries:")
            try:
                keys = list(obj[c].keys())
                print(keys[:40])
            except Exception as e:
                print("Could not enumerate nested keys:", e)
            break

    # If it's already a bare state_dict
    if all(isinstance(k, str) for k in obj.keys()) and len(obj) > 0 and "." in list(obj.keys())[0]:
        print("This dict looks like a bare state_dict (key format contains '.') - sample keys:")
        print(list(obj.keys())[:40])
else:
    print("Unknown object type. repr:")
    print(repr(obj)[:2000])
