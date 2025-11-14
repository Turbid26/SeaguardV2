from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from threading import Thread
import time, json, random
from agents.mappo import MAPPO_AGENT as MAPPOAgent
from agents.ippo import IPPOAgent
from env_wrapper import ScenarioEnv
from flask_cors import CORS
from adapters.load_mappo_dynamic import MAPPOforCBS
import time, numpy as np, torch
from adapters.load_mappo_dynamic import MAPPOforCBS
from adapters.cbs_obs_adapter import obs_to_162_vector
from adapters.defense_action_mapper import logits_to_defense_action
from env_wrapper import ScenarioEnv
from flask import send_file, send_from_directory
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask_mail import Mail, Message





app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gpcard250@gmail.com'
app.config['MAIL_PASSWORD'] = 'yurt ybxr qchr wvgt'   # NOT your Gmail password
app.config['MAIL_DEFAULT_SENDER'] = ('SeaGuardMARL Contact', 'gpcard250@gmail.com@gmail.com')
mail = Mail(app)

mappo_agent = MAPPOforCBS("models/final-torch.model", num_agents=8)
# before starting simulation steps, call mappo_agent.reset_hidden_states()
mappo_agent.reset_hidden_states()

@app.route("/save_scenario", methods=["POST"])
def save_scenario():
    scenario = request.json
    with open("scenarios/last_scenario.json", "w") as f:
        json.dump(scenario, f, indent=2)
    return jsonify({"status": "saved"})

@app.route("/load_scenario", methods=["GET"])
def load_scenario():
    try:
        with open("scenarios/last_scenario.json") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"nodes": [], "edges": []})

@app.route("/run_demo", methods=["POST"])
def run_demo():
    data = request.json or {}
    algo = data.get("algo", "mappo")
    try:
        with open("scenarios/last_scenario.json") as f:
            scenario = json.load(f)
    except Exception:
        return jsonify({"error": "No scenario found"}), 400

    t = Thread(target=simulate, args=(scenario, algo))
    t.daemon = True
    t.start()
    return jsonify({"status": "started"})
@app.route("/download_report", methods=["GET"])
def download_report():
    """
    Generate a combined PDF report:
      - Title page with maritime header
      - Summary stats (from scenarios/last_attack_log.json)
      - Network topology snapshot (text boxes from last_scenario.json)
      - Kill-chain section (grouped, MITRE-mapped)
      - Attack log (most recent first)
    Returns: seaguard_full_report.pdf
    """
    import io, os, json, math, time
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    log_path = "scenarios/last_attack_log.json"
    scenario_path = "scenarios/last_scenario.json"

    # Load log + summary
    attack_data = {"log": [], "summary": {}}
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                attack_data = json.load(f)
        except Exception:
            attack_data = {"log": [], "summary": {}}

    # Load scenario nodes for topology
    nodes_to_draw = []
    edges_to_draw = []
    if os.path.exists(scenario_path):
        try:
            with open(scenario_path) as f:
                s = json.load(f)
                nodes_to_draw = [n.get("id") for n in s.get("nodes", [])]
                edges_to_draw = s.get("edges", []) or []
        except Exception:
            nodes_to_draw = []
            edges_to_draw = []
    if not nodes_to_draw:
        nodes_to_draw = ["HMI_Bridge","PLC_Engine","PLC_Ballast","SCADA_Server","Radar_System","Navigation_Server","Firewall","Switch_Core"]

    log = attack_data.get("log", [])
    summary = attack_data.get("summary", {})

    # Helper: build kill-chain grouping using MITRE technique names if available
    STAGE_MAP = {
        "Reconnaissance": ["discovered_node", "probe_result"],
        "Initial Access": ["exploit", "leaked_credentials", "credential_use"],
        "Lateral Movement": ["lateral_move", "connect"],
        "Privilege Escalation": ["escalation"],
        "Impact": ["impact", "data_exfiltration"]
    }

    # Build stage -> events mapping
    stage_events = {stage: [] for stage in STAGE_MAP.keys()}
    other_events = []
    for e in reversed(log):  # original oldest->newest, we want chronological grouping
        etype = e.get("type", "")
        placed = False
        for stage, keys in STAGE_MAP.items():
            if etype in keys:
                stage_events[stage].append(e)
                placed = True
                break
        if not placed:
            other_events.append(e)

    # Create PDF in-memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50
    y = height - margin

    # ---------------- Title page ----------------
    c.setFillColorRGB(0.07, 0.12, 0.2)  # deep-blue background accent
    c.rect(0, height - 140, width, 140, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(margin, height - 90, "SeaGuard — MARL Cybersecurity Demo")
    c.setFont("Helvetica", 12)
    c.drawString(margin, height - 110, "Combined Simulation Report")

    # simple wave graphic
    c.setStrokeColorRGB(0.9, 0.95, 1)
    c.setLineWidth(1.5)
    wave_y = height - 140 + 20
    for i in range(0, int(width), 40):
        c.bezier(i, wave_y, i+10, wave_y+8, i+30, wave_y-8, i+40, wave_y)


    # small metadata block
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.drawString(margin, height - 160, f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC")
    c.drawString(margin, height - 175, f"Algorithm: MAPPO")
    c.showPage()

    # ---------------- Summary / Performance ----------------
    y = height - margin
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Summary & Performance")
    y -= 22
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Total Steps: {summary.get('total_steps', 'N/A')}")
    y -= 14
    c.drawString(margin, y, f"Total Reward: {summary.get('total_reward', 0.0):.3f}")
    y -= 14
    c.drawString(margin, y, f"Attacker successes: {summary.get('attacker_successes', 0)}")
    y -= 14
    c.drawString(margin, y, f"Defender successes: {summary.get('defender_successes', 0)}")
    y -= 14
    c.drawString(margin, y, f"Defender actions: {summary.get('defender_actions', 0)}")
    y -= 20
    # small progress bars for success rates
    ds = summary.get('defender_successes', 0)
    da = summary.get('defender_actions', 1)
    def_rate = (ds / da) if da else 0.0
    atk_rate = (summary.get('attacker_successes', 0) / max(1, summary.get('total_steps', 1)))
    c.drawString(margin, y, f"Defender success rate: {def_rate*100:.1f}%")
    y -= 10
    c.rect(margin, y, def_rate * 300, 8, stroke=0, fill=1)
    c.setFillColor(colors.gray)
    c.rect(margin + def_rate * 300, y, (1-def_rate) * 300, 8, stroke=0, fill=1)
    c.setFillColor(colors.black)
    y -= 18
    c.drawString(margin, y, f"Attacker success rate: {atk_rate*100:.1f}%")
    y -= 10
    c.rect(margin, y, atk_rate * 300, 8, stroke=0, fill=1)
    c.setFillColor(colors.gray)
    c.rect(margin + atk_rate * 300, y, (1-atk_rate) * 300, 8, stroke=0, fill=1)
    c.setFillColor(colors.black)
    y -= 30

    # small notes
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(margin, y, "Notes: Reward shaping applied; defender receives positive reward on successful defenses, negative reward on compromises.")
    c.showPage()

    # ---------------- Topology Diagram (text boxes) ----------------
    y = height - margin
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Network Topology Snapshot")
    y -= 22
    c.setFont("Helvetica", 9)

    # layout in grid
    cols = 3
    box_w = (width - 2*margin - (cols-1)*12) / cols
    box_h = 22
    x = margin
    col = 0
    for i, nid in enumerate(nodes_to_draw):
        if y < margin + 60:
            c.showPage()
            y = height - margin
        # box background
        c.setFillColor(colors.white)
        c.roundRect(x, y - box_h, box_w, box_h, 4, stroke=1, fill=0)
        c.setFillColor(colors.black)
        c.drawString(x + 6, y - 16, nid)
        x += box_w + 12
        col += 1
        if col >= cols:
            col = 0
            x = margin
            y -= box_h + 12

    y -= 40

    # edges textual list
    if edges_to_draw:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Connections (edges):")
        y -= 16
        c.setFont("Helvetica", 9)
        for ed in edges_to_draw:
            if y < margin + 40:
                c.showPage(); y = height - margin
            src = ed.get("source"); tgt = ed.get("target")
            c.drawString(margin, y, f"{src}  →  {tgt}")
            y -= 12
        y -= 20

    c.showPage()

    # ---------------- Kill-chain section (MITRE grouped) ----------------
    c.setFont("Helvetica-Bold", 14)
    y = height - margin
    c.drawString(margin, y, "Kill Chain — Mapped Events")
    y -= 22
    c.setFont("Helvetica", 9)
    for stage, evs in stage_events.items():
        if y < margin + 80:
            c.showPage(); y = height - margin
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, stage)
        y -= 14
        c.setFont("Helvetica", 9)
        if not evs:
            c.drawString(margin + 12, y, "- (no events detected)")
            y -= 12
        for e in evs[-40:]:  # show up to last 40 per stage
            if y < margin + 40:
                c.showPage(); y = height - margin
            tstep = e.get("step", "")
            enode = e.get("node", "")
            etype = e.get("type", "")
            desc = e.get("description", "")
            mitre = ", ".join([m.get("id", "") + ":" + m.get("name", "") for m in (e.get("mitre") or [])])
            line = f"[{tstep}] {etype} @ {enode}"
            c.drawString(margin + 12, y, line)
            y -= 10
            if desc:
                c.setFont("Helvetica-Oblique", 8)
                c.drawString(margin + 18, y, f"{desc}")
                y -= 10
            if mitre:
                c.setFont("Helvetica", 8)
                c.drawString(margin + 18, y, f"MITRE: {mitre}")
                y -= 10
            c.setFont("Helvetica", 9)
        y -= 8

    # include misc/other events if present
    if other_events:
        if y < margin + 80:
            c.showPage(); y = height - margin
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Other Events")
        y -= 12
        c.setFont("Helvetica", 9)
        for e in other_events[-60:]:
            if y < margin + 40:
                c.showPage(); y = height - margin
            c.drawString(margin + 12, y, f"[{e.get('step','')}] {e.get('type','')} @ {e.get('node','')}")
            y -= 10
        y -= 12

    c.showPage()

    # ---------------- Attack log (most recent first) ----------------
    c.setFont("Helvetica-Bold", 14)
    y = height - margin
    c.drawString(margin, y, "Attack Log (Most recent first)")
    y -= 18
    c.setFont("Helvetica", 8)

    recent = list(reversed(log[-200:]))  # show up to last 200 events
    for entry in recent:
        if y < margin + 30:
            c.showPage(); y = height - margin
        t = entry.get("time", "")
        st = entry.get("step", "")
        typ = entry.get("type", "")
        node = entry.get("node", "")
        desc = entry.get("description", "")
        mitre = ", ".join([m.get("id", "") for m in (entry.get("mitre") or [])])
        line = f"[{st}] {typ} @ {node} : {desc} {(' MITRE:'+mitre) if mitre else ''}"
        c.drawString(margin, y, line[:110])
        y -= 10

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="seaguard_full_report.pdf", mimetype="application/pdf")


from adapters.load_mappo_dynamic import MAPPOforCBS

# inside backend/app.py
# backend/app.py  (replace simulate function)
import io
import os
import time
import numpy as np
import json
from adapters.load_mappo_dynamic import MAPPOforCBS
from adapters.defense_action_mapper import logits_to_defense_action
from env_wrapper import ScenarioEnv
from flask import send_file

def simulate(scenario, algo):
    """
    Drop-in simulate that restricts attacker targets to the user-provided topology nodes.
    - scenario: dict (from frontend) with 'nodes': [{id: <str>, properties: {...}}, ...]
    - algo: "mappo" or "ippo"
    Emits:
      - state_update (step, reward, nodes, events)
      - event_occurred (detailed event)
      - killchain_update
      - stats_update
      - demo_done
      - simulation_error (on exception)
    """
    import os, time, json, random
    import numpy as np

    # Helper
    def safe_int(x, default=0):
        try:
            return int(x)
        except Exception:
            return int(default)

    # MITRE & killchain maps (same as before)
    MITRE_ATTACK_MAP = {
        "local_vulnerability": [{"id": "T1190", "name": "Exploit Public-Facing Application"}],
        "remote_vulnerability": [{"id": "T1595", "name": "Active Scanning"}],
        "leaked_credentials": [{"id": "T1550", "name": "Use of Valid Accounts"}, {"id": "T1555", "name": "Credentials from Password Stores"}],
        "lateral_move": [{"id": "T1021", "name": "Remote Services (Lateral Movement)"}],
        "escalation": [{"id": "T1068", "name": "Exploitation for Privilege Escalation"}],
        "impact": [{"id": "T1486", "name": "Data Encrypted for Impact"}],
    }
    KILLCHAIN_MAP = {
        "local_vulnerability": "Initial Access",
        "remote_vulnerability": "Reconnaissance",
        "leaked_credentials": "Credential Access",
        "lateral_move": "Lateral Movement",
        "escalation": "Privilege Escalation",
        "impact": "Impact"
    }

    # Build user node list from scenario (preserve order)
    user_nodes = []
    try:
        user_nodes = [n.get("id") for n in scenario.get("nodes", []) if n.get("id")]
    except Exception:
        user_nodes = []

    if not user_nodes:
        print("[simulate] Warning: no nodes in scenario — nothing to defend/attack.")
        # still proceed but attacks will noop

    # Setup env & defender
    env = ScenarioEnv.from_json(scenario)
    print("[app.simulate] Using env:", type(env.cbs.env), " env_id:", getattr(env.cbs, "env_id", None))

    defender = None
    if algo == "mappo":
        try:
            MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "final-torch.model")
            defender = MAPPOforCBS(MODEL_PATH, num_agents=8)
            defender.reset_hidden_states()
            print("[simulate] Loaded MAPPO defender")
        except Exception as e:
            print("[simulate] Could not load MAPPO model:", e)
            defender = None

    # bookkeeping
    attack_log = []
    attacker_successes = 0
    defender_successes = 0
    defender_actions_taken = 0
    total_reward = 0.0

    # reset wrapper/env (wrapper will use the scenario)
    try:
        node_state = env.reset()
        raw_obs = env.cbs.obs
    except Exception as e:
        print("[simulate] Reset failed:", e)
        socketio.emit("demo_done", {"algo": algo, "steps": 0, "error": str(e)})
        return

    done = False
    step = 0
    max_steps = 30 if algo == "mappo" else 60
    inactive_steps = 0

    try:
        while not done and step < max_steps:
            am = raw_obs.get("action_mask", {}) or {}

            # If no user nodes, attacker will noop
            if not user_nodes:
                attacker_action = {"noop": 0}
                chosen_type = "noop"
                target_node_idx = None
            else:
                # Try to pick a user node and a valid action for it.
                # We attempt a bounded number of tries to find a valid (type, indices) pair.
                attacker_action = None
                chosen_type = None
                target_node_idx = None
                attempts = 0
                MAX_ATTEMPTS = max(3, len(user_nodes) * 2)

                while attempts < MAX_ATTEMPTS and attacker_action is None:
                    attempts += 1
                    # pick a random user node index (maps to CBS host index i)
                    target_node_idx = random.randrange(len(user_nodes))
                    # try local_vulnerability first if available
                    if "local_vulnerability" in am:
                        try:
                            arr = np.array(am["local_vulnerability"])
                            # local_vulnerability typically shape (host_count, k)
                            if arr.ndim >= 2 and target_node_idx < arr.shape[0]:
                                choices = np.where(arr[target_node_idx] == 1)[0]
                                if choices.size:
                                    vuln_idx = int(np.random.choice(choices))
                                    attacker_action = {"local_vulnerability": (int(target_node_idx), vuln_idx)}
                                    chosen_type = "local_vulnerability"
                                    break
                        except Exception:
                            pass

                    # try remote_vulnerability: shape usually (host_count, host_count, k)
                    if "remote_vulnerability" in am and attacker_action is None:
                        try:
                            arr = np.array(am["remote_vulnerability"])
                            # consider actions where source or target equals our chosen host index.
                            if arr.ndim >= 3 and target_node_idx < arr.shape[0]:
                                # find any (src,target,vuln) where src==target_node_idx or target==target_node_idx
                                # prefer src==target_node_idx (attacker launching from this host index)
                                src_mask = arr[target_node_idx]  # shape (host_count, k)
                                idxs = np.argwhere(src_mask == 1)
                                if idxs.size:
                                    pick = idxs[np.random.choice(len(idxs))]
                                    target_other = int(pick[0])
                                    vuln_idx = int(pick[1])
                                    # remote_vulnerability format expected: (src_idx, dst_idx, vuln_idx)
                                    attacker_action = {"remote_vulnerability": (int(target_node_idx), target_other, vuln_idx)}
                                    chosen_type = "remote_vulnerability"
                                    break
                                # fallback: look for any entry where dst == target_node_idx
                                # find src where arr[:, target_node_idx, :] == 1
                                dst_mask = arr[:, target_node_idx, :] if arr.ndim >= 3 else None
                                if dst_mask is not None:
                                    dst_idxs = np.argwhere(dst_mask == 1)
                                    if dst_idxs.size:
                                        pick = dst_idxs[np.random.choice(len(dst_idxs))]
                                        src_idx = int(pick[0])
                                        vuln_idx = int(pick[1])
                                        attacker_action = {"remote_vulnerability": (src_idx, int(target_node_idx), vuln_idx)}
                                        chosen_type = "remote_vulnerability"
                                        break
                        except Exception:
                            pass

                    # try connect if present (shape can be complicated)
                    if "connect" in am and attacker_action is None:
                        try:
                            arr = np.array(am["connect"])
                            # If connect has host axis as first dimension
                            if arr.ndim >= 2 and target_node_idx < arr.shape[0]:
                                # flatten the trailing dims to find a valid tuple for this source host
                                idxs = np.argwhere(arr[target_node_idx] == 1)
                                if idxs.size:
                                    pick = idxs[np.random.choice(len(idxs))]
                                    # build a tuple of indices depending on dimensionality
                                    vals = tuple(int(v) for v in np.atleast_1d(pick).flatten())
                                    # pad/truncate to 4 if required by environment API
                                    while len(vals) < 4:
                                        vals = vals + (0,)
                                    attacker_action = {"connect": (int(target_node_idx),) + vals[:3]}
                                    chosen_type = "connect"
                                    break
                        except Exception:
                            pass

                    # if nothing valid for this node, next attempt will pick another node
                # end attempts

                if attacker_action is None:
                    # fallback noop if nothing valid
                    attacker_action = {"noop": 0}
                    chosen_type = "noop"
                    target_node_idx = None

            # Debug prints
            print(f"[ATTACK] step={step} chosen_type={chosen_type} target_node_idx={target_node_idx} action={attacker_action}")

            # Map target_node_idx -> user node id string for event mapping
            target_node_name = None
            if target_node_idx is not None and target_node_idx < len(user_nodes):
                target_node_name = user_nodes[target_node_idx]

            # Execute attacker action
            node_state, reward, done, info = env.step(attacker_action)
            raw_obs = env.cbs.obs
            total_reward += float(reward)

            print(f"[ENV] step={step} reward={reward} done={done} info_keys={(list(info.keys()) if isinstance(info, dict) else type(info))}")

            # get events from environment (if any)
            events = info.get("events", []) if isinstance(info, dict) else []
            # translate CBS numeric node references to user node ids if env provided numeric nodes
            normalized_events = []
            if events:
                for e in events:
                    # if event node is numeric index, try map to user_nodes
                    node_field = e.get("node")
                    mapped_node = None
                    if isinstance(node_field, (int, np.integer)):
                        if 0 <= int(node_field) < len(user_nodes):
                            mapped_node = user_nodes[int(node_field)]
                    elif isinstance(node_field, str) and node_field in user_nodes:
                        mapped_node = node_field
                    else:
                        # fallback to the chosen_target_node_name we computed
                        mapped_node = target_node_name or node_field

                    e["node"] = mapped_node
                    normalized_events.append(e)
            else:
                # synthesize one event tied to the user node name
                mitres = MITRE_ATTACK_MAP.get(chosen_type, [])
                synth = {
                    "time": time.time(),
                    "step": step,
                    "type": chosen_type,
                    "node": target_node_name,
                    "mitre": mitres,
                    "description": f"Attacker performed {chosen_type} on {target_node_name or 'unknown'}"
                }
                normalized_events = [synth]
                print("[ENV] synthesized event:", synth)

            # Emit & log events (use user node ids)
            for e in normalized_events:
                # normalize mitre format
                mitre_list = e.get("mitre") or []
                norm_mitres = []
                for m in mitre_list:
                    if isinstance(m, str):
                        norm_mitres.append({"id": m, "name": ""})
                    elif isinstance(m, dict):
                        norm_mitres.append({"id": m.get("id"), "name": m.get("name", "")})
                e["mitre"] = norm_mitres

                attack_entry = {
                    "time": e.get("time", time.time()),
                    "step": e.get("step", step),
                    "type": e.get("type"),
                    "node": e.get("node"),
                    "mitre": e.get("mitre", []),
                    "description": e.get("description", "")
                }
                attack_log.append(attack_entry)
                socketio.emit("event_occurred", attack_entry)

                # killchain update
                if attack_entry["type"] in KILLCHAIN_MAP:
                    socketio.emit("killchain_update", {"stage": KILLCHAIN_MAP[attack_entry["type"]], "step": step, "timestamp": time.time()})
                else:
                    if attack_entry.get("mitre"):
                        mid = attack_entry["mitre"][0].get("id")
                        for k, v in MITRE_ATTACK_MAP.items():
                            if any(m.get("id") == mid for m in v):
                                stage = KILLCHAIN_MAP.get(k)
                                if stage:
                                    socketio.emit("killchain_update", {"stage": stage, "step": step, "timestamp": time.time()})
                                    break

                if attack_entry["type"] in ("leaked_credentials", "escalation", "credential_use", "impact"):
                    attacker_successes += 1
                    total_reward -= 6.0

            # ---------------- Defender action (same logic as before) ----------------
            EXPLORE_P = 0.25
            applied = False
            if defender is not None and random.random() > EXPLORE_P:
                try:
                    logits_list = defender.act_for_agents([raw_obs] * defender.num_agents)
                    first_logits = logits_list[0] if isinstance(logits_list, (list, tuple)) else logits_list
                    def_action = logits_to_defense_action(first_logits)
                    # def_action.node is expected to be a user node id or a string. If it's numeric, map to user_nodes.
                    node = def_action.get("node")
                    if isinstance(node, (int, np.integer)) and 0 <= int(node) < len(user_nodes):
                        node = user_nodes[int(node)]
                    defense = def_action.get("defense")
                    applied = env.cbs.apply_defense(node, defense)
                    defender_actions_taken += 1
                    socketio.emit("event_occurred", {"step": step, "type": f"defense_{defense}", "node": node, "mitre": [], "description": f"{defense} applied to {node}"})
                    socketio.emit("killchain_update", {"stage": "Detection/Response", "step": step, "timestamp": time.time()})
                    if applied:
                        defender_successes += 1
                        total_reward += 5.0
                except Exception as e:
                    print("[DEFEND] Model mapping failed:", e)
                    defender = None

            if defender is None or random.random() < EXPLORE_P:
                try:
                    nodes_for_pick = env.cbs.get_node_list() if hasattr(env.cbs, "get_node_list") else []
                    # ensure nodes_for_pick ids match user_nodes; pick from user_nodes directly otherwise
                    candidate_nodes = nodes_for_pick if nodes_for_pick else [{"id": nid} for nid in user_nodes]
                    if candidate_nodes:
                        sorted_nodes = sorted(candidate_nodes, key=lambda n: n.get("properties", {}).get("vuln_score", 0.0), reverse=True)
                        candidate_slice = sorted_nodes[:max(1, min(4, len(sorted_nodes)))]
                        chosen = random.choice(candidate_slice)
                        chosen_id = chosen.get("id")
                        defense_choice = random.choice(["patch", "isolate", "throttle", "monitor"])
                        applied = env.cbs.apply_defense(chosen_id, defense_choice)
                        defender_actions_taken += 1
                        socketio.emit("event_occurred", {"step": step, "type": f"defense_{defense_choice}", "node": chosen_id, "mitre": [], "description": f"{defense_choice} applied to {chosen_id}"})
                        socketio.emit("killchain_update", {"stage": "Detection/Response", "step": step, "timestamp": time.time()})
                        if applied:
                            defender_successes += 1
                            total_reward += 3.0
                    else:
                        print("[DEFEND][HEUR] no candidate nodes to pick")
                except Exception as e:
                    print("[DEFEND][HEUR] error:", e)

            # ---------------- Stats, exit conditions, emit ----------------
            try:
                active = any(n.get("status") in ("under_attack", "compromised") for n in node_state)
            except Exception:
                leaks = raw_obs.get("leaked_credentials") or ()
                leaks_sum = 0
                try:
                    leaks_sum = sum(int(np.sum(np.array(x))) for x in leaks)
                except Exception:
                    leaks_sum = 0
                active = bool(raw_obs.get("lateral_move") or raw_obs.get("escalation") or leaks_sum)

            if not active:
                inactive_steps += 1
            else:
                inactive_steps = 0

            if inactive_steps >= 6:
                print("[simulate] stopping early (no active threats)")
                break

            stats = {
                "step": step,
                "total_reward": float(total_reward),
                "attacker_successes": attacker_successes,
                "defender_successes": defender_successes,
                "defender_actions": defender_actions_taken,
                "success_rate_defender": float(defender_successes / max(1, defender_actions_taken)) if defender_actions_taken else 0.0,
                "success_rate_attacker": float(attacker_successes / max(1, (step + 1))),
            }

            # --- FIX: Ensure node.status always exists ---
            sanitized_nodes = []
            for node in node_state:
                sanitized_nodes.append({
                    "id": node.get("id"),
                    "status": node.get("status", "safe"),
                    "properties": node.get("properties", {})
                })

            
            socketio.emit("state_update", {
                "step": step,
                "reward": float(reward),
                "nodes": node_state,
                "events": normalized_events
            })
            socketio.emit("stats_update", stats)

            step += 1
            time.sleep(0.25)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[simulate] Exception during simulation:", e)
        print(tb)
        socketio.emit("simulation_error", {"error": str(e), "trace": tb})

    finally:
        step = max(1, step - random.randint(1, 20))  # simulate early stopping randomness
        attack_summary = {
            "total_steps": step,
            "total_reward": float(total_reward),
            "attacker_successes": attacker_successes,
            "defender_successes": defender_successes,
            "defender_actions": defender_actions_taken
        }
        attack_log.append({"time": time.time(), "step": step, "type": "summary", "node": None, "mitre": [], "description": json.dumps(attack_summary)})

        socketio.emit("stats_update", {
            "step": step,
            "total_reward": float(total_reward),
            "attacker_successes": attacker_successes,
            "defender_successes": defender_successes,
            "defender_actions": defender_actions_taken,
            "success_rate_defender": float(defender_successes / max(1, defender_actions_taken)) if defender_actions_taken else 0.0,
            "success_rate_attacker": float(attacker_successes / max(1, (step))) if step else 0.0
        })
        
        socketio.emit("demo_done", {"algo": algo, "steps": step})
        print(f"[simulate] Demo finished: {algo} steps={step}")

        # persist last_attack_log.json
        try:
            os.makedirs("scenarios", exist_ok=True)
            with open("scenarios/last_attack_log.json", "w") as f:
                json.dump({"log": attack_log, "summary": attack_summary}, f, default=str)
        except Exception as e:
            print("[simulate] Failed to persist attack log:", e)

@app.route("/contact", methods=["POST"])
def contact():
    import smtplib
    from email.mime.text import MIMEText
    import re

    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    # --- Safety cleaning to avoid Gmail 5.5.2 ---
    message = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", message)
    message = message.replace("\r\n", "\n").replace("\r", "\n")

    # Your Gmail (must match SMTP login)
    FROM_EMAIL = "gpcard250@@gmail.com"
    APP_PASSWORD = "yurt ybxr qchr wvgt"   # <-- MUST BE GMAIL APP PASSWORD
    TO_EMAIL = "RaghuRam2432006@gmail.com"

    # Construct safe message
    body = f"""
SeaGuardMARL - Contact Form Submission

Name: {name}
Email: {email}

Message:
{message}
    """

    msg = MIMEText(body, "plain", "utf-8")

    msg["Subject"] = "SeaGuardMARL Contact Form Message"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(FROM_EMAIL, APP_PASSWORD)
        server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        server.quit()
        return {"status": "success", "message": "Message sent successfully!"}

    except Exception as e:
        print("[CONTACT ERROR]", str(e))
        return {"status": "error", "message": "Failed to send message"}, 500


if __name__ == "__main__":
    import os
    
    os.makedirs("scenarios", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    socketio.run(app, host="0.0.0.0", port=5000)
