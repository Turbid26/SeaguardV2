# backend/probe_envs.py
import gymnasium as gym
import cyberbattle
import cyberbattle._env
import time
import numpy as np

CAND = []
for name in gym.envs.registry:
    if "CyberBattle" in name:
        CAND.append(name)

print("Registered CyberBattle envs:", CAND)

def sample_env(name, steps=3):
    print("\n=== Probing", name, "===")
    try:
        env = gym.make(name)
    except Exception as e:
        print("  cannot make:", e)
        return
    obs, info = env.reset()
    print("  reset obs keys:", list(obs.keys()) if isinstance(obs, dict) else type(obs))
    # show action_mask shapes if present
    if isinstance(obs, dict) and "action_mask" in obs:
        for k, v in obs["action_mask"].items():
            arr = np.array(v)
            print(f"  action_mask[{k}] shape:", arr.shape, "sum:", int(arr.sum()))
    # step a few times with a safe action attempt:
    for i in range(steps):
        # find the first available action across masks
        action = None
        if isinstance(obs, dict) and "action_mask" in obs:
            for k, v in obs["action_mask"].items():
                arr = np.array(v)
                idx = np.argwhere(arr == 1)
                if idx.size:
                    # prepare a valid action format per earlier discoveries
                    r, c = map(int, idx[0]) if idx.ndim == 2 else (int(idx[0]), 0)
                    if k == "local_vulnerability":
                        action = {"local_vulnerability": (r, c)}
                    elif k == "lateral_move":
                        action = {"lateral_move": (r, c)}
                    elif k == "credential_use":
                        action = {"credential_use": (r, c)}
                    if action:
                        break
        if action is None:
            action = {"noop": 0}
        print("  step", i, "action->", action)
        out = env.step(action)
        # gym may return 5-tuple or 4-tuple
        if len(out) == 5:
            obs, reward, term, trunc, info = out
            done = bool(term or trunc)
        else:
            obs, reward, done, info = out
        print("    reward:", reward, "done:", done)
        time.sleep(0.1)
        if done:
            break
    try:
        env.close()
    except:
        pass

for n in CAND:
    sample_env(n, steps=2)
