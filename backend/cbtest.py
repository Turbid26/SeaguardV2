import gymnasium as gym
import cyberbattle
import cyberbattle._env

env = gym.make("CyberBattleToyCtf-v0")
obs, info = env.reset()

print("\n✅ Environment reset worked!")
print("\nRaw Observation keys:")
for k in obs:
    print(" •", k)

print("\nAction mask example (what actions are possible):")
print(obs["action_mask"])

# Take one step with first valid action
import numpy as np

mask = obs["action_mask"]["local_vulnerability"]
valid = np.argwhere(mask == 1)

if len(valid) == 0:
    print("No local_vulnerability actions available.")
else:
    # ✅ Correct: extract row & column, NOT flatten
    r, c = map(int, valid[0])

    action_dict = {"local_vulnerability": (r, c)}
    print("Selected action:", action_dict)

    obs, reward, terminated, truncated, info = env.step(action_dict)

    print("Step executed ✅")
    print("Reward:", reward)
    print("Done:", terminated or truncated)
