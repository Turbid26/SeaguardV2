import React from "react";

export default function MitreTimeline({events}) {
  return (
    <div style={{width:280, padding:12, background:"#07102a", color:"white"}}>
      <h4>MITRE Timeline</h4>
      <div style={{maxHeight:400, overflowY:"auto"}}>
        {events.map((e, i) => (
          <div key={i} style={{marginBottom:8, padding:8, background:"#0f172a", borderRadius:6}}>
            <div style={{fontSize:12, opacity:0.8}}>{e.time || ""}</div>
            <div style={{fontWeight:600}}>{e.node} — {e.type}</div>
            <div style={{fontSize:12, opacity:0.8}}>{e.description}</div>
            <div style={{fontSize:11, marginTop:6}}>MITRE: { (e.mitre || []).map(m=>m.id).join(", ") }</div>
          </div>
        ))}
      </div>
    </div>
  );
}
