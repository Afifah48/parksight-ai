import React, { useEffect, useState } from 'react';
import { fetchRecommendations } from '../api/client';
import { Badge, TrendArrow } from '../components/UI';
import { Sparkles, AlertTriangle, ShieldCheck, Target, Crosshair } from 'lucide-react';

const Operations = () => {
    const [tab, setTab] = useState(0);
    const [recs, setRecs] = useState(null);
    const tabs = ["⚡ Priority Actions", "🔥 Emerging Alerts", "🚔 Deployments", "🎯 Offenders"];

    useEffect(() => {
        fetchRecommendations().then(setRecs);
    }, []);

    if (!recs) return <div className="p-4 text-txt-muted">Loading Operations...</div>;

    const { top_actions = [], emerging_alerts = [], patrol_deployments = [], offender_targets = [], expected_impact = {} } = recs;

    return (
        <div className="flex-1 overflow-y-auto p-4">
            <div className="grid grid-cols-5 gap-3 mb-4">
                {[
                    ["Active Actions", top_actions.length, Sparkles],
                    ["Emerging Alerts", emerging_alerts.length, AlertTriangle],
                    ["Deployments", patrol_deployments.length, ShieldCheck],
                    ["Offender Targets", offender_targets.length, Target],
                    ["Critical Scope", expected_impact.n_critical_in_scope || 0, Crosshair]
                ].map(([l,v,IconComp], i) => (
                    <div key={i} className="card p-3 flex items-center gap-3 anim-fadein" style={{ animationDelay: `${i * 0.05}s` }}>
                        <div className="w-8 h-8 rounded-lg bg-accent-cyan/10 flex items-center justify-center">
                            <IconComp size={16} className="text-accent-cyan"/>
                        </div>
                        <div>
                            <div className="text-lg font-bold text-txt-bright">{v}</div>
                            <div className="text-[9px] text-txt-muted uppercase tracking-wide">{l}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Tabs */}
            <div className="flex gap-0 border-b border-brd mb-4">
                {tabs.map((t, i) => (
                    <button key={i} onClick={() => setTab(i)} className={`px-4 py-2 text-[11px] font-semibold transition-colors ${tab === i ? "text-accent-cyan border-b-2 border-accent-cyan bg-accent-cyan/[0.04]" : "text-txt-muted hover:text-txt-secondary"}`}>
                        {t}
                    </button>
                ))}
            </div>

            <div className="flex flex-col gap-3">
                {tab === 0 && top_actions.map((r, i) => (
                    <div key={i} className="card p-4 anim-fadein" style={{ borderLeftWidth: 3, borderLeftColor: r.priority_band === "Critical" ? "#ef4444" : "#f97316", animationDelay: `${i * .08}s` }}>
                        <div className="flex justify-between items-start">
                            <div>
                                <div className="text-xs font-bold text-txt-bright mb-1">{r.hotspot_name} ({r.police_station})</div>
                                <div className="text-[11px] text-txt-secondary leading-relaxed">{r.reason}</div>
                            </div>
                            <Badge band={r.priority_band} small/>
                        </div>
                    </div>
                ))}

                {tab === 1 && emerging_alerts.map((a, i) => (
                    <div key={i} className="card p-4 anim-fadein" style={{ borderLeftWidth: 3, borderLeftColor: a.urgency === "CRITICAL" ? "#ef4444" : "#f97316", animationDelay: `${i * .08}s` }}>
                        <div className="text-[9px] font-bold uppercase tracking-wide mb-1" style={{ color: a.urgency === "CRITICAL" ? "#ef4444" : "#f97316" }}>🔥 DRIFT SCORE: {a.drift_score?.toFixed(1)}</div>
                        <div className="text-xs font-bold text-txt-bright">{a.hotspot_name}</div>
                        <div className="text-[11px] text-txt-secondary mt-1">{a.recommended_action}</div>
                    </div>
                ))}

                {tab === 2 && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {patrol_deployments.map((r, i) => (
                            <div key={i} className="card p-4 anim-fadein" style={{ borderLeftWidth: 3, borderLeftColor: "#3b82f6", animationDelay: `${i * .08}s` }}>
                                <div className="text-xs font-bold text-txt-bright mb-1">{r.police_station}</div>
                                <div className="text-[10px] text-txt-muted mb-1">Critical Hotspots: {r.critical_hotspots}</div>
                                <div className="text-[10px] text-txt-secondary mt-2">{r.deployment_note}</div>
                            </div>
                        ))}
                    </div>
                )}

                {tab === 3 && offender_targets.map((o, i) => (
                    <div key={i} className="card p-4 anim-fadein" style={{ animationDelay: `${i * .08}s` }}>
                        <div className="flex items-center justify-between">
                            <div className="text-sm font-bold font-mono text-accent-cyan">{o.vehicle_number}</div>
                            <div className="text-right">
                                <span className="text-lg font-bold text-status-critical">{o.total_violations}</span>
                                <span className="text-[9px] text-txt-muted ml-1">violations</span>
                            </div>
                        </div>
                        <div className="text-[10px] text-txt-secondary mt-2">Score: {o.offender_score?.toFixed(1)} — Active span: {o.active_span_days} days</div>
                        <div className="text-[10px] text-txt-muted mt-1">{o.intercept_note}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Operations;
