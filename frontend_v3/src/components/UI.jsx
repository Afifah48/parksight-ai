import React from 'react';


export const BAND_COLORS = {Critical:"#ef4444", High:"#f97316", Medium:"#eab308", Low:"#22c55e"};
export const BAND_BG = {Critical:"rgba(239,68,68,0.12)", High:"rgba(249,115,22,0.12)", Medium:"rgba(234,179,8,0.12)", Low:"rgba(34,197,94,0.12)"};

export const Badge = ({band, small}) => {
    const c = BAND_COLORS[band] || "#94a3b8";
    const bg = BAND_BG[band] || "rgba(148,163,184,0.12)";
    return <span className={`inline-block rounded-full font-semibold uppercase tracking-wide border ${small?"text-[9px] px-1.5 py-0":"text-[10px] px-2 py-0.5"}`} style={{color:c, background:bg, borderColor:c+"40"}}>{band}</span>;
};

export const StatusDot = ({color="green", pulse}) => (
    <span className={`inline-block w-2 h-2 rounded-full ${pulse?"animate-pulse":""}`} style={{background:color, boxShadow:`0 0 6px ${color}`}}/>
);

export const ProgressBar = ({value=0, max=100, color="#22c55e", h=4}) => (
    <div className="w-full rounded-full overflow-hidden" style={{height:h, background:"#1e293b"}}>
        <div className="rounded-full transition-all duration-700" style={{width:`${Math.min((value/max)*100, 100)}%`, height:"100%", background:color}}/>
    </div>
);

export const TrendArrow = ({dir="up"}) => {
    const cfg = {up:["↗","#ef4444"], down:["↘","#22c55e"], flat:["→","#64748b"]};
    const [arrow, color] = cfg[dir] || cfg.flat;
    return <span className="font-semibold text-xs" style={{color}}>{arrow}</span>;
};

export const SectionHeader = ({icon: Icon, title, right, border=true}) => (
    <div className={`flex items-center justify-between pb-2 mb-3 ${border?"border-b border-brd":""}`}>
        <div className="flex items-center gap-2">
            {Icon && <Icon size={16} className="text-txt-muted"/>}
            <span className="text-[11px] font-bold uppercase tracking-[0.1em] text-txt-secondary">{title}</span>
        </div>
        {right}
    </div>
);
