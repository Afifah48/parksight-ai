import React, { useEffect, useState } from 'react';
import { fetchHotspots } from '../api/client';
import { Badge, SectionHeader, StatusDot, BAND_COLORS } from '../components/UI';
import LeafletMap from '../components/LeafletMap';
import { Zap, BarChart2 } from 'lucide-react';

const Intelligence = () => {
    const [hotspots, setHotspots] = useState([]);
    const [selected, setSelected] = useState(null);

    useEffect(() => {
        fetchHotspots().then(data => {
            setHotspots(data);
            if (data.length > 0) setSelected(data.sort((a,b)=>b.pcis_score - a.pcis_score)[0]);
        });
    }, []);

    const criticalJunctions = hotspots.filter(h => h.priority_band === "Critical" || h.priority_band === "High").sort((a,b)=>b.pcis_score - a.pcis_score).slice(0, 5);
    
    return (
        <div className="flex-1 flex overflow-hidden">
            <div className="flex-1 flex flex-col p-3 gap-2 min-w-0">
                <LeafletMap markers={hotspots} height="100%" className="flex-1"/>
                <div className="flex items-center gap-3 bg-srf rounded-lg border border-brd px-3 py-2">
                    <span className="text-[10px] font-semibold text-txt-secondary uppercase tracking-wide">Congestion Impact (PCIS)</span>
                    <div className="flex-1 h-1.5 rounded-full" style={{background:"linear-gradient(90deg,#22c55e,#eab308,#f97316,#ef4444)"}}/>
                    <div className="flex gap-8 text-[9px] text-txt-muted"><span>Low</span><span>Severe</span></div>
                </div>
            </div>
            
            <div className="w-[340px] shrink-0 overflow-y-auto p-3 flex flex-col gap-3 border-l border-brd">
                <div className="text-sm font-bold text-txt-bright">Hotspot Analytics</div>
                
                <SectionHeader icon={Zap} title="Critical Junctions"/>
                <table className="w-full text-[11px] mb-4">
                    <thead>
                        <tr className="text-[9px] text-txt-muted uppercase">
                            <th className="text-left pb-2">Junction</th>
                            <th className="text-right pb-2">Violations</th>
                            <th className="text-right pb-2">PCIS</th>
                            <th className="text-center pb-2">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {criticalJunctions.map((h, idx) => (
                            <tr key={idx} className={`border-t border-brd-subtle cursor-pointer transition-colors ${selected?.hotspot_id===h.hotspot_id?"bg-accent-cyan/[0.06]":"hover:bg-srf-hover"}`} onClick={()=>setSelected(h)}>
                                <td className="py-1.5 font-medium">{h.hotspot_name?.slice(0,15)}..</td>
                                <td className="py-1.5 text-right font-mono text-accent-cyan">{h.violation_count?.toLocaleString()}</td>
                                <td className="py-1.5 text-right font-mono" style={{color:BAND_COLORS[h.priority_band]}}>{h.pcis_score?.toFixed(1)}</td>
                                <td className="py-1.5 text-center"><StatusDot color={BAND_COLORS[h.priority_band]}/></td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                {selected && (
                    <div className="card p-3 border-accent-cyan anim-fadein">
                        <div className="flex justify-between items-start mb-2">
                            <div>
                                <div className="text-sm font-bold text-txt-bright">{selected.hotspot_name}</div>
                                <div className="text-[9px] text-txt-muted mt-0.5">{selected.police_station}</div>
                            </div>
                            <Badge band={selected.priority_band} small/>
                        </div>
                        <div className="grid grid-cols-2 gap-2 mb-3">
                            <div className="bg-bg-secondary rounded-lg p-2">
                                <div className="text-[8px] text-txt-muted uppercase">PCIS Score</div>
                                <div className="text-lg font-bold" style={{color:BAND_COLORS[selected.priority_band]}}>{selected.pcis_score?.toFixed(1)}</div>
                            </div>
                            <div className="bg-bg-secondary rounded-lg p-2">
                                <div className="text-[8px] text-txt-muted uppercase">Drift Score</div>
                                <div className="text-lg font-bold text-txt-bright">{selected.drift_score?.toFixed(1)}</div>
                            </div>
                        </div>
                        <p className="text-[10px] text-txt-secondary leading-relaxed mb-3">
                            Total violations: {selected.violation_count?.toLocaleString()}. <br/>
                            Drift status: {selected.drift_status}.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Intelligence;
