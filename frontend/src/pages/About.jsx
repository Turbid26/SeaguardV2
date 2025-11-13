import React, { useState } from "react";
import Navbar from "../components/Navbar";
import "./About.css";  // for carousel styling; create this file
import adityaPic from "./team/aditya.jpg";
// import keerthanPic from "./team/keerthan.jpg";
// import kshitijPic from "./team/kshitij.jpg";
// import raghuPic from "./team/raghu.jpg";
// import sindhuPic from "./team/sindhu.jpg";

const teamMembers = [
  { name: "Naga Aditya Sai Kari", role: "23BD1A1242", photo: adityaPic, bio: "Built stable interfaces between CyberBattleSim environments and SeaGuardMARL’s learning agents" },
  { name: "Narra Keerthan Reddy", role: "23BD1A1243", photo: "/team/keerthan.jpg", bio: "Developed and maintained the backend services powering SeaGuardMARL’s real-time simulation engine." },
  { name: "Allimaganla Kshitij Raj", role: "23BD1A1204", photo: "/team/kshitij.jpg", bio: "Implemented environment logic, node mappings, and event pipelines enabling realistic threat simulations." },
  { name: "Raghuram Thiguti", role: "23BD1A1224", photo: "/team/raghu.jpg", bio: "Developed and trained core multi-agent reinforcement learning models for maritime cyber-defense." },
  { name: "Sindhu Sri", role: "23BD1A0579", photo: "/team/sindhu.jpg", bio: "Designed interactive visualizations and UI for maritime defense analytics." }
];

export default function About() {
  const [current, setCurrent] = useState(0);

  const nextMember = () => {
    setCurrent((current + 1) % teamMembers.length);
  };

  const prevMember = () => {
    setCurrent((current - 1 + teamMembers.length) % teamMembers.length);
  };

  const member = teamMembers[current];

  return (
    <>
      <Navbar />
      <div style={{ padding: 30, color: "white", maxWidth: 900, margin: "0 auto" }}>
        <h1>About SeaGuard MARL</h1>
        <p>
          SeaGuard MARL is a next-generation platform for maritime operational-technology cybersecurity.
          It integrates multi-agent reinforcement learning with realistic simulation of industrial control
          networks on board ships and offshore platforms. Our system models both attacker and defender agents,
          applies MITRE ATT&CK tactics through simulated adversarial campaigns, and visualizes state changes
          in a maritime-specific network topology.
        </p>
        <p>
          The core innovation lies in translating maritime control-system assets (HMIs, PLCs, SCADA servers,
          radar, navigation systems) into graph-based environments and enabling a defender agent (using
          MAPPO/IPPO) to dynamically protect critical nodes while the attacker executes lateral movement,
          credential theft, and command-and-control attacks. We provide actionable insights into alert
          probabilities, vulnerability scores, and attack paths, backed by downloadable PDF reports and
          interactive timelines.
        </p>

         <div className="links">
          <a
            href="https://arxiv.org/abs/2409.06008" 
            target="_blank"
            rel="noreferrer"
            className="link-btn"
          >
            📄 Read the Research Paper            
          </a>
            <p></p>
          <a
            href="https://github.com/your-repo-here"
            target="_blank"
            rel="noreferrer"
            className="link-btn"
          >
            🛠️ View GitHub Repository
          </a>
        </div>
        <h2>Meet the Team</h2>
        
        <div className="carousel">
          <button className="nav left" onClick={prevMember}>&lt;</button>
          <div className="member-card">
            <img src={member.photo} alt={member.name} className="member-photo" />
            <h3>{member.name}</h3>
            <h4>{member.role}</h4>
            <p>{member.bio}</p>
          </div>
          <button className="nav right" onClick={nextMember}>&gt;</button>
        </div>

        <p style={{ marginTop: 60 }}>
          Together, we are committed to protecting maritime infrastructures from evolving cyber threats,
          combining real-world ICS knowledge, reinforcement-learning expertise, and interactive visualization.
        </p>
      </div>
    </>
  );
}
