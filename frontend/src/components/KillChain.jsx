import React from "react";

const stages = [
  { key: "recon", label: "Reconnaissance", mitre: ["T1595", "T1590"] },
  { key: "resource", label: "Resource Development", mitre: ["T1583", "T1584"] },
  { key: "initial_access", label: "Initial Access", mitre: ["T1190", "T1133"] },
  { key: "execution", label: "Execution", mitre: ["T1059", "T1203"] },
  { key: "persistence", label: "Persistence", mitre: ["T1547", "T1136"] },
  { key: "privilege_escalation", label: "Privilege Escalation", mitre: ["T1068"] },
  { key: "defense_evasion", label: "Defense Evasion", mitre: ["T1070", "T1562"] },
  { key: "credential_access", label: "Credential Access", mitre: ["T1555", "T1550"] },
  { key: "discovery", label: "Discovery", mitre: ["T1046", "T1082"] },
  { key: "lateral_movement", label: "Lateral Movement", mitre: ["T1021"] },
  { key: "command_control", label: "Command & Control", mitre: ["T1071"] },
  { key: "impact", label: "Impact", mitre: ["T1486"] }
];

export default function KillChain({ events }) {
  const triggered = new Set();
  events.forEach(ev => {
    ev.mitre?.forEach(m => triggered.add(m.id));
  });

  return (
    <div style={{ marginTop: 20 }}>
      <h3>MITRE Attack Chain</h3>

      {stages.map((s, i) => {
        const active = s.mitre.some(id => triggered.has(id));

        return (
          <div key={s.key} style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: active ? "#ef4444" : "#334155",
                marginRight: 8,
                boxShadow: active ? "0 0 8px 2px red" : "none",
                transition: "0.3s"
              }}
            ></div>
            <div style={{ fontSize: 14, opacity: active ? 1 : 0.5 }}>
              {i + 1}. {s.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}
