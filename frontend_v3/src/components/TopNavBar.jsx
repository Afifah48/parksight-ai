import React from 'react';
import { Search, Bell, Settings, HelpCircle, AlertTriangle } from 'lucide-react';
import { StatusDot } from './UI';

const TopNavBar = ({title=""}) => (
    <nav className="bg-bg-secondary/80 backdrop-blur-md border-b border-brd flex justify-between items-center w-full px-4 h-14 shrink-0 z-50">
        <div className="flex items-center gap-4">
            <span className="text-lg font-extrabold text-txt-bright tracking-tight">ParkSight AI</span>
            {title && <><div className="h-5 w-px bg-brd mx-1"/><span className="text-[10px] font-semibold text-txt-muted uppercase tracking-[0.1em] bg-srf px-2.5 py-1 rounded border border-brd">{title}</span></>}
            <div className="hidden md:flex items-center ml-3 gap-1.5 bg-srf px-3 py-1.5 rounded-lg border border-brd focus-within:border-accent-cyan transition-colors">
                <Search size={16} className="text-txt-muted"/>
                <input className="bg-transparent border-none text-txt-DEFAULT text-xs focus:ring-0 focus:outline-none w-52 placeholder:text-txt-muted" placeholder="Search operational data..."/>
            </div>
        </div>
        <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-srf px-3 py-1.5 rounded border border-brd">
                <StatusDot color="#22c55e" pulse/>
                <span className="text-[10px] font-semibold text-status-low uppercase tracking-wider">System Live</span>
            </div>
            <button className="bg-critical-bg border border-status-critical/40 text-status-critical px-3 py-1 rounded text-[10px] font-bold uppercase tracking-wide hover:bg-status-critical/20 transition-colors flex items-center gap-1">
                <AlertTriangle size={14}/> Emergency
            </button>
            <div className="flex items-center gap-1 text-txt-muted border-l border-brd pl-3">
                <button className="p-1.5 hover:bg-srf-hover rounded transition-colors"><Bell size={18}/></button>
                <button className="p-1.5 hover:bg-srf-hover rounded transition-colors"><Settings size={18}/></button>
                <button className="p-1.5 hover:bg-srf-hover rounded transition-colors"><HelpCircle size={18}/></button>
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent-blue to-accent-indigo flex items-center justify-center text-[10px] text-white font-bold ml-1">U</div>
            </div>
        </div>
    </nav>
);
export default TopNavBar;
