import React, { useState, useCallback, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Landing from "./pages/Landing";
import About from "./pages/About";
import Contact from "./pages/Contact";
import UserManual from "./pages/Manual";
import Playground from "./pages/Playground";

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ background: "#0f172a", minHeight: "100vh" }}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/manual" element={<UserManual />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
