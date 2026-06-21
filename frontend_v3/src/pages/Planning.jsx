import React, { useEffect, useState } from 'react';
import { fetchRoutes, fetchHotspots } from '../api/client';
import { SectionHeader, Badge } from '../components/UI';
import LeafletMap from '../components/LeafletMap';
import { Route, MapPin } from 'lucide-react';

const Planning = () => {
    const [routes, setRoutes] = useState([]);
    const [hotspots, setHotspots] = useState([]);
    const [activeStation, setActiveStation] = useState(null);

    useEffect(() => {
        fetchRoutes().then(setRoutes);
        fetchHotspots().then(setHotspots);
    }, []);

    // Extract unique stations to serve as a proxy for 'zones'
    const stations = [...new Set(routes.map(r => r.police_station))];

    // Get the route coords for the active station
    let activeRouteId = null;
    let routeCoords = [];
    if (routes.length > 0) {
        const stationToUse = activeStation || stations[0];
        const stationRoutes = routes.filter(r => r.police_station === stationToUse);
        if (stationRoutes.length > 0) {
            activeRouteId = stationRoutes[0].route_id;
            routeCoords = routes.filter(r => r.route_id === activeRouteId).map(r => [r.latitude, r.longitude]);
        }
    }

    return (
        <div className="flex-1 flex overflow-hidden">
            {/* Sidebar */}
            <div className="w-[300px] shrink-0 overflow-y-auto p-4 border-r border-brd bg-bg-secondary flex flex-col gap-4">
                <div>
                    <h1 className="text-xl font-bold text-txt-bright">Patrol Planner</h1>
                    <p className="text-xs text-txt-secondary mt-1">Algorithmic route generation targeting high-impact zones.</p>
                </div>
                
                <SectionHeader icon={Route} title="Generated Routes" />
                
                <div className="flex flex-col gap-3">
                    {stations.slice(0, 10).map((station, i) => {
                        const stationRoutes = routes.filter(r => r.police_station === station);
                        const uniqueRoutes = new Set(stationRoutes.map(r => r.route_id)).size;
                        return (
                            <div key={i} 
                                 className={`card p-3 hover:border-accent-cyan cursor-pointer transition-colors ${activeStation === station ? 'border-accent-cyan bg-accent-cyan/[0.05]' : ''}`}
                                 onClick={() => setActiveStation(station)}>
                                <div className="text-sm font-bold text-txt-bright mb-1">{station}</div>
                                <div className="text-xs text-txt-secondary mb-2">Generated Routes: {uniqueRoutes}</div>
                                <div className="flex items-center gap-2">
                                    <Badge band="High" small />
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Map Area */}
            <div className="flex-1 p-4 flex flex-col min-w-0">
                <div className="flex-1 card overflow-hidden border border-brd relative">
                    <LeafletMap markers={hotspots} height="100%" showHeat={false} routeCoords={routeCoords} />
                    <div className="absolute top-4 left-4 z-[400] bg-srf/90 backdrop-blur border border-brd p-3 rounded-lg shadow-xl w-64 pointer-events-none">
                        <div className="text-xs font-bold text-txt-bright mb-2 flex items-center gap-2">
                            <MapPin size={14} className="text-accent-cyan" />
                            Route Configuration
                        </div>
                        <div className="flex justify-between text-[10px] text-txt-secondary py-1 border-b border-brd-subtle">
                            <span>Total Routes</span>
                            <span className="font-bold text-txt-bright">{new Set(routes.map(r => r.route_id)).size}</span>
                        </div>
                        <div className="flex justify-between text-[10px] text-txt-secondary py-1 border-b border-brd-subtle">
                            <span>Total Stops</span>
                            <span className="font-bold text-txt-bright">{routes.length}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Planning;
