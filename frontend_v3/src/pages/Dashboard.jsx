import React, { useEffect, useState } from 'react';
import { fetchKpis, fetchHotspots, fetchRecommendations } from '../api/client';
import { Badge, SectionHeader } from '../components/UI';
import LeafletMap from '../components/LeafletMap';
import { Activity, AlertTriangle, Layers, MapPin } from 'lucide-react';

const VitalCard = ({ label, value, sub, trend, trendDir }) => (
    <div className="card p-3 anim-fadein">
        <div className="text-[9px] font-bold uppercase tracking-[0.08em] text-txt-muted mb-1">{label}</div>
        <div className="text-xl font-extrabold text-txt-bright leading-tight">{value}</div>
        {sub && <div className="text-[10px] text-txt-secondary mt-1">{sub}</div>}
        {trend && <div className={`text-[10px] font-semibold mt-1 ${trendDir==="up"?"text-status-critical":trendDir==="down"?"text-status-low":"text-txt-muted"}`}>{trend}</div>}
    </div>
);

const Dashboard = () => {
    const [kpis, setKpis] = useState(null);
    const [hotspots, setHotspots] = useState([]);
    const [recs, setRecs] = useState(null);

    useEffect(() => {
        fetchKpis().then(setKpis);
        fetchHotspots().then(setHotspots);
        fetchRecommendations().then(setRecs);
    }, []);

    if (!kpis) return <div className="p-4 text-txt-muted">Loading Dashboard...</div>;

    const topH = hotspots.filter(h => h.priority_band === "Critical" || h.priority_band === "High").slice(0, 6);
    const topActions = recs?.top_actions || [];

    return (
        <div className="flex-1 flex overflow-hidden">
            {/* Vital Signs */}
            <div className="w-[240px] shrink-0 overflow-y-auto p-3 flex flex-col gap-2 border-r border-brd">
                <SectionHeader icon={Activity} title="Vital Signs" />
                <VitalCard label="Total Violations" value={kpis.total_violations?.toLocaleString() || 0} />
                <VitalCard label="Critical Hotspots" value={kpis.critical_hotspots} sub="Active Intervention Required" />
                <VitalCard label="Emerging Hotspots" value={kpis.emerging_hotspots} sub="Predictive model flag" />
                <VitalCard label="Repeat Offenders" value={kpis.repeat_offenders} />
                <VitalCard label="Total Patrol Routes" value={kpis.patrol_routes} sub="Active patrol coverage" />
            </div>

            {/* Center — Map + Tables */}
            <div className="flex-1 flex flex-col overflow-hidden p-3 gap-3 min-w-0">
                <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-txt-bright">Bengaluru Ops Live</span>
                    <div className="flex gap-2 text-txt-muted">
                        <Layers size={16} />
                        <MapPin size={16} />
                    </div>
                </div>
                <div className="flex-1 rounded-lg overflow-hidden border border-brd min-h-[300px]">
                    <LeafletMap markers={hotspots} height="100%" showHeat />
                </div>
                <div className="flex gap-3 h-[220px] shrink-0">
                    <div className="flex-1 card p-3 overflow-auto">
                        <SectionHeader icon={AlertTriangle} title="Top Priority Hotspots" border={false} />
                        <table className="w-full text-[11px]">
                            <thead>
                                <tr className="text-[9px] text-txt-muted uppercase tracking-wide">
                                    <th className="text-left pb-2">Location</th>
                                    <th className="text-center pb-2">Risk Lvl</th>
                                    <th className="text-right pb-2">Violations</th>
                                </tr>
                            </thead>
                            <tbody>
                                {topH.map((h, idx) => (
                                    <tr key={idx} className="border-t border-brd-subtle hover:bg-accent-cyan/[0.03] transition-colors">
                                        <td className="py-1.5 text-txt-DEFAULT font-medium">{h.hotspot_name}</td>
                                        <td className="py-1.5 text-center"><Badge band={h.priority_band} small /></td>
                                        <td className="py-1.5 text-right font-mono text-accent-cyan font-medium">{h.violation_count?.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Tactical Feed */}
            <div className="w-[290px] shrink-0 overflow-y-auto p-3 flex flex-col gap-3 border-l border-brd">
                <div className="text-sm font-bold text-txt-bright">Tactical Feed</div>
                {topActions.map((r, i) => (
                    <div key={i} className="card p-3 anim-fadein" style={{ animationDelay: `${i * 0.1}s` }}>
                        <div className="text-xs font-bold text-txt-bright mb-1">{r.hotspot_name}</div>
                        <div className="text-[10px] text-txt-secondary leading-relaxed mb-2">{r.reason}</div>
                        <button className="text-[10px] font-semibold px-3 py-1 rounded bg-accent-cyan text-bg hover:opacity-80 transition-opacity">
                            {r.action_type}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Dashboard;
