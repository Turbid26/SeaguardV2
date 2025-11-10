import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Navbar from "../components/Navbar";
import React, { useState, useCallback, useEffect } from "react";
// import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import WaveFooter from "../components/WaveFooter";

export default function Landing() {
  return (
    <div className="landing-container">
      
      {/* Glowing Logo + Title */}
      <motion.h1
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        className="hero-title"
      >
        SeaGuard MARL
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 1 }}
        className="hero-sub"
      >
        Maritime Network Defense using Multi-Agent Reinforcement Learning
      </motion.p>

      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="hero-buttons"
      >
        <Link to="/playground" className="btn primary">Launch Playground</Link>
        <Link to="/manual" className="btn secondary">View User Manual</Link>
      </motion.div>

      {/* Animated Wave Footer */}
      <WaveFooter />
    </div>
  );
}
