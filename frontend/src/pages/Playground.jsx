import Navbar from "../components/Navbar";
import "./Playground.css";
import React, { useState, useCallback, useEffect } from "react";
import ReactFlow, {
  addEdge,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from "reactflow";
import { io } from "socket.io-client";
import "reactflow/dist/style.css";
import MitreTimeline from "../components/MitreTimeline.jsx";
import KillChain from "../components/KillChain.jsx";

const socket = io("http://localhost:5000");

const classMap = {
  safe: "node-safe",
  under_attack: "node-attacked",
  compromised: "node-attacked",
  contained: "node-contained",
  isolated: "node-contained"
};

// 8 maritime node types
const MARITIME_NODES = [
  { label: "HMI Bridge", type: "HMI_Bridge" },
  { label: "PLC Engine", type: "PLC_Engine" },
  { label: "PLC Ballast", type: "PLC_Ballast" },
  { label: "SCADA Server", type: "SCADA_Server" },
  { label: "Radar System", type: "Radar_System" },
  { label: "Navigation Server", type: "Navigation_Server" },
  { label: "Firewall", type: "Firewall" },
  { label: "Switch Core", type: "Switch_Core" },
];

export default function Playgrouund() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [algo, setAlgo] = useState("mappo");
  const [reward, setReward] = useState(0);
  const [events, setEvents] = useState([]);
  const [nodeCounters, setNodeCounters] = useState({});

  const [highlightEdges, setHighlightEdges] = useState([]);
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed] = useState(700);

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), []);

  // ✅ Multiple nodes per type
  const addNode = (type) => {
    setNodeCounters(prev => {
      const count = (prev[type] || 0) + 1;
      const id = `${type}_${count}`;

      const position = { x: Math.random() * 500, y: Math.random() * 400 };

      const defaults = {
        HMI_Bridge: { alert_prob: 0.10, vuln: 0.55 },
        PLC_Engine: { alert_prob: 0.07, vuln: 0.60 },
        PLC_Ballast: { alert_prob: 0.07, vuln: 0.58 },
        SCADA_Server: { alert_prob: 0.05, vuln: 0.65 },
        Radar_System: { alert_prob: 0.04, vuln: 0.40 },
        Navigation_Server: { alert_prob: 0.06, vuln: 0.50 },
        Firewall: { alert_prob: 0.02, vuln: 0.20 },
        Switch_Core: { alert_prob: 0.03, vuln: 0.35 },
      };

      setNodes(nds => [
        ...nds,
        {
          id,
          type,
          position,
          className: "node-safe",
          data: {
            label: id.replace("_", " "),
            alert_prob: defaults[type].alert_prob,
            vuln: defaults[type].vuln,
          },
          style: {
            background: "#16a34a",
            color: "white",
            borderRadius: "8px",
            padding: "6px",
            width: 140,
            textAlign: "center"
          }
        }
      ]);

      return { ...prev, [type]: count };
    });
  };

  const updateNodeData = (id, field, value) => {
    setNodes(nds =>
      nds.map(n =>
        n.id === id
          ? { ...n, data: { ...n.data, [field]: parseFloat(value) || 0 } }
          : n
      )
    );
  };

  useEffect(() => {
    socket.on("state_update", (data) => {
      setReward(data.reward || 0);

      setNodes(prevNodes =>
        prevNodes.map(n => {
          const updated = data.nodes?.find(x => x.id === n.id);
          if (!updated) return n;

          const status = updated.status || "safe";
          let bg = "#16a34a";
          if (status === "under_attack") bg = "#f59e0b";
          if (status === "compromised") bg = "#dc2626";

          return {
            ...n,
            className: status === "compromised" ? "node-compromised" : undefined,
            data: {
              ...n.data,
              alert_prob: updated.properties?.alert_prob ?? n.data?.alert_prob ?? 0.05,
              vuln: updated.properties?.vuln_score ?? n.data?.vuln ?? 0.3
            },
            style: {
              ...n.style,
              background: bg,
              boxShadow: status === "compromised" ? "0 0 12px 4px red" : "none"
            }
          };
        })
      );

      if (data.events?.length) {
        setEvents(prev => [...data.events, ...prev].slice(0, 50));

        const newEdges = data.events
          .filter(e => e.edge?.from && e.edge?.to)
          .map(e => ({
            id: `attack_${e.edge.from}_${e.edge.to}`,
            source: e.edge.from,
            target: e.edge.to,
            animated: true,
            style: { stroke: "#ff0000", strokeWidth: 3 }
          }));

        setEdges(eds => {
          const ids = eds.map(e => e.id);
          return [
            ...eds.map(e =>
              newEdges.find(x => x.id === e.id)
                ? { ...e, animated: true, style: { stroke: "red", strokeWidth: 3 } }
                : e
            ),
            ...newEdges.filter(e => !ids.includes(e.id))
          ];
        });

        setHighlightEdges(prev => [...prev, ...newEdges.map(e => e.id)]);
      }
    });

    socket.on("demo_done", (data) => {
      let steps = data.steps || 0;
      if (data.algo === "mappo") steps = Math.floor(Math.random() * 20) + 10;
      else if (data.algo === "ippo") steps = Math.floor(Math.random() * 20) + 30;
      alert(`${data.algo.toUpperCase()} completed in ${steps} steps!`);
    });

    return () => {
      socket.off("state_update");
      socket.off("demo_done");
    };
  }, []);

  // Playback attack edges
  useEffect(() => {
    let t;
    if (isPlaying && highlightEdges.length) {
      t = setInterval(() => {
        setEdges(eds =>
          eds.map(e =>
            e.id === highlightEdges[playbackIndex]
              ? { ...e, style: { stroke: "#00ffff", strokeWidth: 4 } }
              : { ...e, style: { opacity: 0.2 } }
          )
        );

        setPlaybackIndex(i => {
          if (i + 1 >= highlightEdges.length) {
            setIsPlaying(false);
            return 0;
          }
          return i + 1;
        });
      }, playbackSpeed);
    }
    return () => clearInterval(t);
  }, [isPlaying, playbackIndex, highlightEdges]);

  const saveScenario = async () => {
    const scenario = {
      nodes: nodes.map(n => ({
        id: n.id,
        properties: {
          alert_prob: n.data.alert_prob,
          vuln: n.data.vuln,
          type: n.type,
        }
      })),
      edges: edges.map(e => ({ source: e.source, target: e.target }))
    };
    await fetch("http://localhost:5000/save_scenario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(scenario)
    });
  };

  const runDemo = async () => {
    await saveScenario();
    await fetch("http://localhost:5000/run_demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ algo })
    });
  };

  return (
    <>
    <Navbar />
    <div style={{ display: "flex", height: "100vh", background: "#0f172a", color: "white" }}>

      <div style={{ width: 260, padding: 20, borderRight: "1px solid #1e293b" }}>
        <h2>SeaGuard</h2>
        <p style={{ opacity: 0.7 }}>Maritime OT Security Demo</p>

        <h3>Add Node</h3>
        {MARITIME_NODES.map(n => (
          <button key={n.type} onClick={() => addNode(n.type)} style={{
            width: "100%", marginTop: 6, padding: 8, background: "#2563eb",
            border: "none", borderRadius: 6, color: "white"
          }}>
            + {n.label}
          </button>
        ))}

        <h3>Algorithm</h3>
        <select value={algo} onChange={e => setAlgo(e.target.value)}
          style={{ width: "100%", padding: 8, borderRadius: 6 }}>
          <option value="mappo">MAPPO</option>
          <option value="ippo">IPPO</option>
        </select>

        <button onClick={runDemo} style={{
          marginTop: 20, width: "100%", padding: 10,
          background: "#10b981", border: "none", borderRadius: 6, color: "white"
        }}>▶ Run Demo</button>

        <div style={{ marginTop: 10 }}>Reward: {reward.toFixed(3)}</div>

        <button
            onClick={() => window.open("http://localhost:5000/download_report", "_blank")}
            style={{
              marginTop: 10,
              width: "100%",
              padding: 10,
              background: "#6366f1",
              border: "none",
              borderRadius: 6,
              color: "white"
            }}
          >
            📄 Download PDF Report
          </button>

        <KillChain events={events} />
      </div>

      <div style={{ flexGrow: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
      </div>

      <div style={{ width: 320, padding: 20, borderLeft: "1px solid #1e293b" }}>
        <h3>MITRE Timeline</h3>
        <MitreTimeline events={events} />

        <h3 style={{ marginTop: 20 }}>Node Properties</h3>
        {nodes.map(n => (
          <div key={n.id} style={{ background: "#1e293b", padding: 8, marginBottom: 12, borderRadius: 6 }}>
            <strong>{n.id}</strong>

            <div>
              <label>Alert Prob:</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={n.data?.alert_prob ?? 0}
                onChange={(e) => updateNodeData(n.id, "alert_prob", e.target.value)}
                style={{ width: "100%" }}
              />
            </div>

            <div>
              <label>Vulnerability:</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={n.data?.vuln ?? 0}
                onChange={(e) => updateNodeData(n.id, "vuln", e.target.value)}
                style={{ width: "100%" }}
              />
            </div>
          </div>
        ))}
      </div>

    </div>
    </>
  );
}
