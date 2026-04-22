
---

# 🚢 SeaGuardMARL

### Autonomous Multi-Agent Cyber Defense for Maritime Operational Technology

---

## 📌 Overview

**SeaGuardMARL** is an interactive cyber-defense simulation platform designed for **maritime Operational Technology (OT) systems**. It combines **Multi-Agent Reinforcement Learning (MARL)** with a customizable cyber-range to simulate attacker–defender interactions in realistic industrial environments.

Unlike traditional rule-based systems, SeaGuardMARL models both attackers and defenders as adaptive agents, enabling dynamic and realistic cybersecurity experimentation.

---

## 🎯 Key Features

* 🧠 **Multi-Agent RL (MAPPO/IPPO)** for autonomous cyber defense
* 🌐 **CyberBattleSim-based environment** extended for maritime OT systems
* 🎨 **Interactive topology builder** using ReactFlow
* ⚡ **Real-time simulation visualization** (attacks, defenses, node states)
* 🛡️ **MITRE ATT&CK mapping + Kill Chain tracking**
* 📊 **Automated PDF report generation** with attack analytics
* 🔁 **Event-driven architecture** with real-time updates via Socket.IO

---

## 🏗️ System Architecture

SeaGuardMARL consists of three core components:

### 1. Backend (Flask + Simulation Engine)

* Handles simulation execution and API endpoints
* Integrates CyberBattleSim with maritime extensions
* Runs MARL inference (MAPPO/IPPO)
* Emits real-time events via Socket.IO

### 2. Frontend (React + ReactFlow)

* Drag-and-drop topology creation
* Real-time visualization of attacks and defenses
* MITRE timeline and kill-chain tracking

### 3. AI Module (PyTorch)

* MAPPO/IPPO models for defense strategies
* Observation processing and action mapping

---

## 🔁 Simulation Workflow

1. User designs a maritime network topology
2. Backend converts topology into simulation environment
3. Attacker and defender agents interact in real time
4. Events are mapped to MITRE ATT&CK techniques
5. Results are visualized and exported as reports

---

## 🧰 Tech Stack

| Layer      | Technologies                |
| ---------- | --------------------------- |
| Frontend   | React, ReactFlow, Socket.IO |
| Backend    | Flask, Flask-SocketIO       |
| AI         | PyTorch (MAPPO/IPPO)        |
| Simulation | CyberBattleSim              |
| Storage    | JSON scenarios + logs       |
| Reporting  | ReportLab (PDF)             |

---

## ⚙️ Setup Instructions

### 1. Clone Dependencies

```bash
git clone https://github.com/microsoft/CyberBattleSim.git
```

---

### 2. Python Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

```bash
cd backend
pip install -r requirements.txt
```

---

### 3. Install CyberBattleSim

```bash
cd CyberBattleSim
pip install -e .
```

---

### 4. Frontend Setup

```bash
cd frontend
npm install
```

---

### 5. Run Application

```bash
# Backend
cd backend
python app.py

# Frontend
cd frontend
npm run dev
```

---

## 📡 API Endpoints

| Endpoint               | Description                |
| ---------------------- | -------------------------- |
| `POST /save_scenario`  | Save user-defined topology |
| `POST /run_demo`       | Run simulation             |
| `GET /download_report` | Download PDF report        |

---

## 🔄 Real-Time Events

* `state_update` → Node status changes
* `event_occurred` → MITRE-mapped events
* `stats_update` → Simulation metrics
* `killchain_update` → Kill-chain progression
* `demo_done` → Simulation completed

---

## 🧪 AI & Defense System

### Supported Algorithms

* **MAPPO** (Centralized training, coordinated defense)
* **IPPO** (Independent agents)

### Defense Actions

* Patch
* Isolate
* Monitor
* Throttle

---

## 🧠 MITRE ATT&CK Integration

Each attack/defense event is mapped to MITRE techniques:

| Action           | MITRE ID |
| ---------------- | -------- |
| Exploit          | T1190    |
| Recon            | T1595    |
| Lateral Movement | T1021    |
| Escalation       | T1068    |
| Impact           | T1486    |

---

## 📊 Output & Reports

The system generates detailed PDF reports including:

* Attack timeline
* Node compromise statistics
* MITRE technique coverage
* Defense performance metrics
* Network topology summary

---

## 📁 Project Structure

```
SeaGuardMARL/
│
├── backend/
│   ├── agents/
│   ├── adapters/
│   ├── models/
│   ├── scenarios/
│   └── app.py
│
├── frontend/
│   ├── src/
│   ├── components/
│   └── pages/
│
├── CyberBattleSim/   (external dependency)
└── README.md
```

---

## 💻 System Requirements

### Software

* Python 3.10+
* Node.js
* PyTorch
* Flask + SocketIO
* CyberBattleSim

### Hardware

* Minimum: **8GB RAM**
* Optional: GPU for RL training

---

## 🚀 Use Cases

* Cybersecurity research (MARL-based defense)
* Maritime OT system simulation
* Cyber-range training environments
* Adversarial attack/defense experimentation

---

## 🔮 Future Work

* High-fidelity maritime process simulation
* Advanced RL models (GNNs, hierarchical RL)
* Multi-user cloud deployment
* Enhanced attacker modeling
* 3D visualization and replay systems

---

## 📚 References

* CyberBattleSim – Microsoft Research
* MITRE ATT&CK Framework
* MAPPO / PPO Research Papers
* Maritime Cybersecurity Standards

---

## 🤝 Contributing

Contributions are welcome. Please open issues or submit pull requests for improvements.

---

## 📌 Author

**Raghuram Thiguti**
GitHub: [https://github.com/Turbid26](https://github.com/Turbid26)

---

