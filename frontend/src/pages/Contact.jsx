import Navbar from "../components/Navbar";
import React, { useState, useCallback, useEffect } from "react";
export default function Contact() {
  return (
    <>
      <Navbar />
      <div style={{ padding: 30, color: "white" }}>
        <h1>Contact Us</h1>
        <p>Email: support@seaguardmarl.ai</p>
        <p>GitHub: github.com/yourrepo</p>
      </div>
    </>
  );
}
