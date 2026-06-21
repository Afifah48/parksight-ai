import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Lightbulb, Shield, AlertTriangle, Car, Route, LineChart, Settings, HelpCircle, Plus } from 'lucide-react';

const SideNavBar = () => {
    const location = useLocation();
    const nav = [
        {path:"/", icon: LayoutDashboard, label:"Executive"},
        {path:"/intelligence", icon: Lightbulb, label:"Intelligence"},
        {path:"/operations", icon: Shield, label:"Operations"},
        {path:"/analytics", icon: AlertTriangle, label:"Emerging Threats"},
        {path:"/vehicle-intel", icon: Car, label:"Vehicle Intel"},
        {path:"/planning", icon: Route, label:"Planning"},
        {path:"/simulator", icon: LineChart, label:"Simulator"},
    ];
    return (
        <aside className="bg-bg-secondary border-r border-brd h-full w-sidebar shrink-0 flex-col hidden md:flex">
            <div className="p-3 border-b border-brd flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-accent-blue to-accent-indigo flex items-center justify-center"><span className="text-white text-sm">🛡️</span></div>
                <div><div className="text-sm font-bold text-txt-bright">BTP Command</div><div className="text-[9px] text-txt-muted uppercase tracking-[0.12em]">Operational Intelligence</div></div>
            </div>
            <div className="px-3 py-2.5">
                <button className="w-full bg-gradient-to-r from-accent-blue to-accent-cyan text-white py-2 rounded-lg text-[11px] font-semibold flex items-center justify-center gap-1.5 hover:opacity-90 transition-opacity">
                    <Plus size={15}/> New Patrol Plan
                </button>
            </div>
            <nav className="flex-1 overflow-y-auto py-1 flex flex-col gap-0.5">
                {nav.map(n => {
                    const active = location.pathname===n.path;
                    const IconComponent = n.icon;
                    return (
                        <Link key={n.path} to={n.path} className={`flex items-center px-3 py-2 mx-1 rounded-r-lg transition-all text-[11px] font-semibold ${active?"text-accent-cyan bg-accent-cyan/8 border-l-[3px] border-accent-cyan":"text-txt-secondary hover:bg-srf-hover border-l-[3px] border-transparent"}`}>
                            <IconComponent size={18} className="mr-3"/>{n.label}
                        </Link>
                    );
                })}
            </nav>
            <div className="border-t border-brd p-2 flex flex-col gap-0.5">
                <button className="flex items-center px-3 py-2 text-txt-secondary text-[11px] hover:bg-srf-hover rounded transition-colors"><Settings size={16} className="mr-3"/>Settings</button>
                <button className="flex items-center px-3 py-2 text-txt-secondary text-[11px] hover:bg-srf-hover rounded transition-colors"><HelpCircle size={16} className="mr-3"/>Support</button>
            </div>
        </aside>
    );
};
export default SideNavBar;
