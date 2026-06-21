import React, { useEffect, useState } from 'react';
import { fetchOffenders } from '../api/client';
import { SectionHeader, StatusDot } from '../components/UI';
import { Car, Search } from 'lucide-react';

const VehicleIntel = () => {
    const [offenders, setOffenders] = useState([]);
    const [search, setSearch] = useState("");

    useEffect(() => {
        fetchOffenders().then(setOffenders);
    }, []);

    const filtered = offenders.filter(o => o.vehicle_number?.toLowerCase().includes(search.toLowerCase()));

    return (
        <div className="flex-1 flex flex-col overflow-hidden p-4">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-xl font-bold text-txt-bright">Vehicle Intelligence</h1>
                    <p className="text-xs text-txt-secondary mt-0.5">Tracking and enforcement for chronic repeat offenders.</p>
                </div>
            </div>
            
            <div className="flex gap-4 mb-4">
                <div className="flex items-center gap-2 bg-srf px-3 py-2 rounded-lg border border-brd w-64">
                    <Search size={16} className="text-txt-muted"/>
                    <input 
                        type="text" 
                        value={search}
                        onChange={(e)=>setSearch(e.target.value)}
                        placeholder="Search vehicle number..." 
                        className="bg-transparent border-none text-sm text-txt-DEFAULT focus:outline-none w-full"
                    />
                </div>
            </div>

            <div className="flex-1 card overflow-auto p-4">
                <SectionHeader icon={Car} title="Top Repeat Offenders" />
                <table className="w-full text-left text-sm">
                    <thead>
                        <tr className="text-xs text-txt-muted uppercase border-b border-brd">
                            <th className="pb-2">Vehicle Number</th>
                            <th className="pb-2">Total Violations</th>
                            <th className="pb-2">Peak Violations</th>
                            <th className="pb-2">Primary Station</th>
                            <th className="pb-2">Offender Score</th>
                            <th className="pb-2">Active Span (Days)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map((o, i) => (
                            <tr key={i} className="border-b border-brd-subtle hover:bg-srf-hover transition-colors">
                                <td className="py-2 font-mono text-accent-cyan font-bold">{o.vehicle_number}</td>
                                <td className="py-2 font-mono">{o.total_violations}</td>
                                <td className="py-2 font-mono text-txt-secondary">{o.peak_hour_violations}</td>
                                <td className="py-2">{o.top_station}</td>
                                <td className="py-2 font-mono font-bold" style={{ color: o.offender_score > 80 ? "#ef4444" : "#f97316" }}>{o.offender_score?.toFixed(1)}</td>
                                <td className="py-2">{o.active_span_days}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default VehicleIntel;
