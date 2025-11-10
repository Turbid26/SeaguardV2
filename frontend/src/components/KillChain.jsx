import React from "react";

const stages = [
  { key: "recon", label: "Reconnaissance", mitre: ["T1595"] },
  { key: "weapon", label: "Weaponization", mitre: [] },
  { key: "deliver", label: "Delivery", mitre: ["T1190"] },
  { key: "exploit", label: "Exploitation", mitre: ["T1068"] },
  { key: "install", label: "Installation", mitre: [] },
  { key: "c2", label: "C2 / Lateral", mitre: ["T1021", "T1550"] },
  { key: "impact", label: "Impact", mitre: ["T1486"] },
];

const KillChain = ({ events }) => {
  // Collect triggered MITRE IDs from timeline events
  const triggered = new Set();
  events.forEach(ev => {
    ev.mitre?.forEach(m => triggered.add(m.id));
  });

  return (
    <div style={{ marginTop: 20 }}>
      <h3>Kill Chain</h3>

      {stages.map((s, i) => {
        const active = s.mitre.some(id => triggered.has(id));

        return (
          <div
            key={s.key}
            style={{
              display: "flex",
              alignItems: "center",
              marginBottom: 8,
            }}
          >
            {/* Circle */}
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: active ? "#ef4444" : "#334155",
                marginRight: 8,
                boxShadow: active ? "0 0 8px 2px red" : "none",
                transition: "0.3s",
              }}
            />

            {/* Label */}
            <div style={{ fontSize: 14, opacity: active ? 1 : 0.5 }}>
              {i + 1}. {s.label}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default KillChain;
