import React, { useEffect, useState } from 'react';
import { fetchEmerging } from '../api/client';
import { SectionHeader, StatusDot } from '../components/UI';
import { AlertTriangle, TrendingUp } from 'lucide-react';

const EmergingThreats = () => {
    const [emerging, setEmerging] = useState([]);

    useEffect(() => {
        fetchEmerging().then(setEmerging);
    }, []);

    if (!emerging) return <div className="p-4 text-txt-muted">Loading Emerging Threats...</div>;

    const criticalCount = emerging.filter(e => e.drift_score > 75).length;

    return (
        <div className="flex-1 overflow-y-auto p-4">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-xl font-bold text-txt-bright">Emerging Threat Center</h1>
                    <p className="text-xs text-txt-secondary mt-0.5">Real-time identification of accelerating congestion risks.</p>
                </div>
            </div>
            
            <div className="grid grid-cols-12 gap-3">
                {/* Active Hotspots Sidebar */}
                <div className="col-span-3 flex flex-col gap-3">
                    <SectionHeader icon={AlertTriangle} title="Active Hotspots" right={<span className="text-[9px] font-bold bg-status-critical text-white px-2 py-0.5 rounded-full">{criticalCount} CRITICAL</span>} />
                    {emerging.filter(e => e.drift_score > 75).slice(0, 5).map((e, i) => (
                        <div key={i} className="card p-3 anim-fadein" style={{ borderLeftWidth: 3, borderLeftColor: "#ef4444", animationDelay: `${i * .08}s` }}>
                            <div className="flex justify-between">
                                <span className="text-[8px] font-bold uppercase text-status-critical">Critical Drift</span>
                            </div>
                            <div className="text-[11px] font-semibold text-txt-bright mt-1">{e.hotspot_name}</div>
                            <div className="text-[10px] text-txt-secondary mt-0.5">Drift Score: {e.drift_score?.toFixed(1)}</div>
                        </div>
                    ))}
                </div>

                {/* Rankings Table */}
                <div className="col-span-9">
                    <SectionHeader icon={TrendingUp} title="Emerging Hotspot Rankings" />
                    <div className="card p-3">
                        <table className="w-full text-[11px]">
                            <thead>
                                <tr className="text-[9px] text-txt-muted uppercase tracking-wide">
                                    <th className="text-left pb-2">Location Name</th>
                                    <th className="text-left pb-2">Station</th>
                                    <th className="text-right pb-2">Drift Score</th>
                                    <th className="text-center pb-2">Status</th>
                                    <th className="text-right pb-2">Violations</th>
                                </tr>
                            </thead>
                            <tbody>
                                {emerging.slice(0, 15).map((h, i) => (
                                    <tr key={i} className="border-t border-brd-subtle hover:bg-accent-cyan/[0.03] transition-colors">
                                        <td className="py-1.5 font-medium">{h.hotspot_name}</td>
                                        <td className="py-1.5 text-txt-secondary">{h.police_station}</td>
                                        <td className="py-1.5 text-right font-mono font-bold" style={{ color: h.drift_score > 75 ? "#ef4444" : "#f97316" }}>{h.drift_score?.toFixed(1)}</td>
                                        <td className="py-1.5 text-center"><StatusDot color={h.drift_score > 75 ? "#ef4444" : "#f97316"} /></td>
                                        <td className="py-1.5 text-right font-mono">{h.violation_count?.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EmergingThreats;
