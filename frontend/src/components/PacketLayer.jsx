import React, {useEffect, useState} from "react";

export default function PacketLayer({events, nodePositions}) {
  // events: list of {step, type, node, ...}
  const [packets, setPackets] = useState([]);

  useEffect(() => {
    if (!events || !events.length) return;
    const ev = events[0]; // newest first
    // pick a target position based on nodePositions map (id -> {x,y})
    const target = nodePositions?.[ev.node];
    const start = {x: 20, y: 40}; // attacker "internet" origin
    const packet = {
      id: Date.now() + Math.random(),
      start,
      target: target || {x: Math.random()*600, y: Math.random()*300},
      created: Date.now()
    };
    setPackets(p => [...p, packet]);

    // remove after animation
    const to = setTimeout(()=> {
      setPackets(p => p.filter(pp => pp.id !== packet.id));
    }, 1200);
    return () => clearTimeout(to);
  }, [events]);

  return (
    <div style={{position:"absolute", left:0, top:0, right:0, bottom:0, pointerEvents:"none"}}>
      {packets.map(pk => {
        // simple CSS animation using inline style with transition
        const elapsed = Math.min(1, (Date.now() - pk.created) / 1000);
        const x = pk.start.x + (pk.target.x - pk.start.x) * elapsed;
        const y = pk.start.y + (pk.target.y - pk.start.y) * elapsed;
        return <div key={pk.id} className="packet" style={{left:x, top:y}} />;
      })}
    </div>
  );
}
