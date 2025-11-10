import React, {useEffect, useState} from "react";

export default function AnimatedNode({data}) {
  // data: { label, alert_prob, vuln, status }
  const [showShield, setShowShield] = useState(false);
  useEffect(() => {
    if (data && data.lastDefense) {
      // show shield briefly
      setShowShield(true);
      const t = setTimeout(()=>setShowShield(false), 700);
      return () => clearTimeout(t);
    }
  }, [data && data.lastDefense]);

  const baseStyle = {
    padding: 8,
    borderRadius: 8,
    color: "white",
    minWidth: 100,
    textAlign: "center"
  };

  const status = data?.status || "safe";
  const bg = status === "compromised" ? "#b91c1c" : status === "under_attack" ? "#f59e0b" : "#16a34a";
  const classes = status === "under_attack" ? "node-pulse" : status === "compromised" ? "node-compromised-shake" : "";

  return (
    <div className={classes} style={{...baseStyle, background: bg}}>
      <div style={{fontWeight:700}}>{data?.label || "node"}</div>
      <div style={{fontSize:12, opacity:0.9}}>Vuln: {(data?.vuln ?? 0).toFixed(2)}</div>
      <div style={{fontSize:12, opacity:0.9}}>Alert: {(data?.alert_prob ?? 0).toFixed(2)}</div>

      {showShield && (
        <div className="shield-pop" style={{position:"absolute", marginTop:-40, right:8}}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="1.5">
            <path d="M12 2l7 4v6c0 5-4 9-7 10-3-1-7-5-7-10V6l7-4z" />
          </svg>
        </div>
      )}
    </div>
  );
}
