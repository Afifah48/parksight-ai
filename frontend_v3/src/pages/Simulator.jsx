import React, { useEffect, useState } from 'react';
import { fetchRoi } from '../api/client';
import { SectionHeader } from '../components/UI';
import { LineChart, Calculator, BarChart2 } from 'lucide-react';

const Simulator = () => {
    const [roiData, setRoiData] = useState([]);
    const [officers, setOfficers] = useState(5);
    const [intensity, setIntensity] = useState(0.8);

    useEffect(() => {
        fetchRoi().then(setRoiData);
    }, []);

    // Calculation Engine
    let baseline = null;
    let projectedPCISReduction = 0;
    let hotspotsTargeted = 0;
    let patrolVisits = 0;
    let repeatOffendersPrevented = 0;
    let recommendation = "";

    if (roiData.length > 0) {
        // Find nearest baseline scenario
        baseline = [...roiData].sort((a, b) => {
            const distA = Math.abs(a.additional_officers - officers) + Math.abs(a.enforcement_intensity - intensity) * 10;
            const distB = Math.abs(b.additional_officers - officers) + Math.abs(b.enforcement_intensity - intensity) * 10;
            return distA - distB;
        })[0];

        const officerFactor = officers / Math.max(baseline.additional_officers, 1);
        const intensityFactor = intensity / Math.max(baseline.enforcement_intensity, 0.1);

        projectedPCISReduction = Math.min(baseline.projected_pcis_reduction * officerFactor * intensityFactor, 25);
        hotspotsTargeted = Math.min(Math.round(baseline.hotspots_targeted * officerFactor), 701);
        patrolVisits = Math.round(officers * 20 * intensity);
        repeatOffendersPrevented = Math.max(Math.round(baseline.estimated_repeat_offender_reduction * officerFactor * intensityFactor), 0);

        if (officers < 15) {
            recommendation = "Increase officer allocation to improve hotspot coverage.";
        } else if (officers < 35) {
            recommendation = "Balanced deployment. Focus on top-ranked emerging hotspots.";
        } else {
            recommendation = "Maximum enforcement coverage achieved. Prioritize repeat offender suppression.";
        }
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 flex gap-4">
            {/* Controls */}
            <div className="w-80 shrink-0 flex flex-col gap-4">
                <div>
                    <h1 className="text-xl font-bold text-txt-bright">ROI Simulator</h1>
                    <p className="text-xs text-txt-secondary mt-1">Forecast impact based on resource allocation.</p>
                </div>

                <div className="card p-4">
                    <SectionHeader icon={Calculator} title="Parameters" />
                    
                    <div className="mb-4">
                        <div className="flex justify-between text-xs text-txt-secondary mb-2">
                            <span>Patrol Officers</span>
                            <span className="font-mono font-bold text-accent-cyan">{officers}</span>
                        </div>
                        <input 
                            type="range" min="1" max="50" value={officers} 
                            onChange={(e)=>setOfficers(Number(e.target.value))}
                            className="w-full accent-accent-cyan"
                        />
                    </div>

                    <div className="mb-4">
                        <div className="flex justify-between text-xs text-txt-secondary mb-2">
                            <span>Enforcement Intensity</span>
                            <span className="font-mono font-bold text-accent-cyan">{intensity.toFixed(1)}×</span>
                        </div>
                        <input 
                            type="range" min="0.5" max="1.5" step="0.1" value={intensity} 
                            onChange={(e)=>setIntensity(Number(e.target.value))}
                            className="w-full accent-accent-cyan"
                        />
                    </div>
                </div>

                {baseline && (
                    <div className="card p-4 border-status-low">
                        <SectionHeader icon={LineChart} title="Projected Impact" />
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="text-[10px] text-txt-muted uppercase">Hotspots Targeted</div>
                                <div className="text-xl font-bold text-txt-bright">{hotspotsTargeted}</div>
                            </div>
                            <div>
                                <div className="text-[10px] text-txt-muted uppercase">Patrol Visits Added</div>
                                <div className="text-xl font-bold text-txt-bright">{patrolVisits}</div>
                            </div>
                            <div className="col-span-2">
                                <div className="text-[10px] text-txt-muted uppercase">Repeat Offenders Prevented</div>
                                <div className="text-xl font-bold text-txt-bright">{repeatOffendersPrevented}</div>
                            </div>
                            <div className="col-span-2 bg-status-low/10 p-3 rounded-lg border border-status-low/20">
                                <div className="text-[10px] text-txt-muted uppercase">Citywide PCIS Reduction</div>
                                <div className="text-2xl font-bold text-status-low">-{projectedPCISReduction.toFixed(2)} pts</div>
                            </div>
                        </div>
                        
                        <div className="mt-4 p-3 bg-srf-hover border-l-2 border-accent-cyan text-sm text-txt-secondary rounded-r">
                            <span className="font-bold text-txt-bright block mb-1">Recommendation</span>
                            {recommendation}
                        </div>
                    </div>
                )}
            </div>

            {/* Main Area */}
            <div className="flex-1 flex flex-col gap-4 min-w-0">
                <div className="card p-4 flex-1 overflow-auto">
                    <SectionHeader icon={BarChart2} title="Scenario Dictionary" />
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="text-xs text-txt-muted uppercase border-b border-brd">
                                <th className="pb-2">Scenario ID</th>
                                <th className="pb-2 text-right">Officers</th>
                                <th className="pb-2 text-right">Intensity</th>
                                <th className="pb-2 text-right">Hotspots Targeted</th>
                                <th className="pb-2 text-right">PCIS Reduction</th>
                            </tr>
                        </thead>
                        <tbody>
                            {roiData.map((s, i) => (
                                <tr key={i} className={`border-b border-brd-subtle hover:bg-srf-hover transition-colors ${baseline?.scenario_id === s.scenario_id ? 'bg-accent-cyan/10' : ''}`}>
                                    <td className="py-2 font-mono text-txt-secondary">{s.scenario_id}</td>
                                    <td className="py-2 text-right">{s.additional_officers}</td>
                                    <td className="py-2 text-right font-mono">{s.enforcement_intensity?.toFixed(2)}</td>
                                    <td className="py-2 text-right">{s.hotspots_targeted}</td>
                                    <td className="py-2 text-right font-mono font-bold text-status-low">-{s.projected_pcis_reduction?.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Simulator;
