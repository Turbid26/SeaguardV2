import React, { useState } from "react";
import Navbar from "../components/Navbar";
import "./Contact.css";

export default function Contact() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const submitForm = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch("http://localhost:5000/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, message }),
      });

      const data = await res.json();
      alert(data.message);

      if (data.status === "success") {
        setName("");
        setEmail("");
        setMessage("");
      }
    } catch (err) {
      alert("Failed to send. Please try again.");
    }

    setLoading(false);
  };

  return (
    <>
      <Navbar />

      <div className="contact-container">
        <div className="contact-card">
          <h1 className="title">Contact Us</h1>
          <p className="subtitle">
            We'd love to hear from you. Get in touch with the SeaGuardMARL team.
          </p>

          <div className="contact-info">
            <p>
              📧 Email:{" "}
              <a href="mailto:seaguardmarl@gmail.com">
                seaguardmarl@gmail.com
              </a>
            </p>
            <p>
              🛠️ GitHub:{" "}
              <a
                href="https://github.com/Turbid26/SeaguardV2"
                target="_blank"
                rel="noreferrer"
              >
                https://github.com/Turbid26/SeaguardV2
              </a>
            </p>
            
          </div>

          <h2 className="form-title">Send us a message</h2>

          <form className="contact-form" onSubmit={submitForm}>
            <input
              type="text"
              placeholder="Your Name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
            />

            <input
              type="email"
              placeholder="Your Email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <textarea
              placeholder="Your Message"
              rows="4"
              required
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />

            <button type="submit" disabled={loading}>
              {loading ? "Sending..." : "Send Message"}
            </button>
          </form>
        </div>

        {/* Maritime wave footer */}
        <div className="wave"></div>
      </div>
    </>
  );
}
