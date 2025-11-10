import Navbar from "../components/Navbar.jsx";
import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const steps = [
  { title: "Welcome", text: "SeaGuard MARL defends maritime OT networks using Multi-Agent Reinforcement Learning." },
  { title: "Build Network", text: "Add nodes, connect topology, assign vulnerabilities and alert probabilities." },
  { title: "Run Simulation", text: "Launch MAPPO or IPPO agents to defend while attacker attempts MITRE-based compromise." },
  { title: "Analyze", text: "Watch kill-chain, timeline, node compromises, reward curves and defense decisions." },
  { title: "Export", text: "Generate and download PDF reports summarizing attack and defense effectiveness." },
  { title: "Done!", text: "You're ready to secure your maritime cyber-physical infrastructure 🚢" },
];

export default function UserManual() {
  const [index, setIndex] = useState(0);

  return (
    <>
    <Navbar />
    <div className="manual-container">
      <AnimatePresence mode="wait">
        <motion.div
          key={index}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -50 }}
          transition={{ duration: 0.4 }}
          className="manual-card"
        >
          <h2>{steps[index].title}</h2>
          <p>{steps[index].text}</p>
        </motion.div>
      </AnimatePresence>

      <div className="manual-controls">
        <button disabled={index === 0} onClick={() => setIndex(i => i - 1)}>← Prev</button>
        <span>{index + 1} / {steps.length}</span>
        <button disabled={index === steps.length-1} onClick={() => setIndex(i => i + 1)}>Next →</button>
      </div>
    </div>
    </>
  );
}
