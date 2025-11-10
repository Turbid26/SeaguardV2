import { Link } from "react-router-dom";
import React, { useState, useCallback, useEffect } from "react";

import "../index.css"; // ensure global CSS loads (for body styling etc.)

export default function Navbar() {
  return (
    <nav className="navbar">
      <Link className="nav-item" to="/playground">⚓ Playground</Link>
      <Link className="nav-item" to="/about">🌊 About Us</Link>
      <Link className="nav-item" to="/contact">📞 Contact</Link>
      <Link className="nav-item" to="/manual">📘 User Manual</Link>
    </nav>
  );
}

