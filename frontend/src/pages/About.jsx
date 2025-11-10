import Navbar from "../components/Navbar";
import React, { useState, useCallback, useEffect } from "react";

export default function About() {
  return (
    <>
      <Navbar />
      <div style={{ padding: 30, color: "white" }}>
        <h1>About SeaGuardMARL</h1>
        <p>AI-powered maritime OT security using Multi-Agent Reinforcement Learning.</p>
      </div>
    </>
  );
}
