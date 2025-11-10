
import React, { useState, useCallback, useEffect } from "react";
export default function WaveFooter() {
  return (
    <div className="wave-wrapper">
      <svg viewBox="0 0 1440 320" className="wave-svg">
        <path
          fill="#0ea5e9"
          fillOpacity="0.5"
          d="M0,224L60,218.7C120,213,240,203,360,213.3C480,224,600,256,720,240C840,224,960,160,1080,144C1200,128,1320,160,1380,176L1440,192L1440,320L0,320Z"
        />
        <path
          fill="#0369a1"
          fillOpacity="0.7"
          d="M0,256L48,245.3C96,235,192,213,288,224C384,235,480,277,576,261.3C672,245,768,171,864,144C960,117,1056,139,1152,170.7C1248,203,1344,245,1392,266.7L1440,288L1440,320L0,320Z"
        />
        <path
          fill="#0f172a"
          fillOpacity="1"
          d="M0,288L60,293.3C120,299,240,309,360,288C480,267,600,213,720,186.7C840,160,960,160,1080,181.3C1200,203,1320,245,1380,266.7L1440,288L1440,320L0,320Z"
        />
      </svg>
    </div>
  );
}
