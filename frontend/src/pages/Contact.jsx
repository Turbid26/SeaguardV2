import React from "react";
import Navbar from "../components/Navbar";
import "./Contact.css"; // create this file

export default function Contact() {
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
                href="https://github.com/your-repo-here"
                target="_blank"
                rel="noreferrer"
              >
                github.com/your-repo-here
              </a>
            </p>
            <p>
              🌐 Website:{" "}
              <a
                href="https://seaguardmarl.ai"
                target="_blank"
                rel="noreferrer"
              >
                seaguardmarl.ai
              </a>
            </p>
          </div>

          <h2 className="form-title">Send us a message</h2>

          <form className="contact-form">
            <input type="text" placeholder="Your Name" required />
            <input type="email" placeholder="Your Email" required />
            <textarea placeholder="Your Message" rows="4" required />
            <button type="submit">Send Message</button>
          </form>
        </div>

        {/* Maritime wave footer */}
        <div className="wave"></div>
      </div>
    </>
  );
}
