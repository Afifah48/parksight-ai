import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { BAND_COLORS } from './UI';

const LeafletMap = ({ markers=[], center=[12.9716, 77.5946], zoom=12, height="100%", showHeat=true, routeCoords, className="" }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);

    useEffect(() => {
        if (!L) return; // Ensure Leaflet is loaded
        if (mapInstanceRef.current) { mapInstanceRef.current.remove(); mapInstanceRef.current = null; }
        if (!mapRef.current) return;
        
        const map = L.map(mapRef.current, { zoomControl: true, attributionControl: false }).setView(center, zoom);
        L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 19 }).addTo(map);
        
        markers.forEach(m => {
            const c = BAND_COLORS[m.priority_band || m.band] || "#3b82f6";
            const name = m.hotspot_name || m.name || 'Unknown';
            const v = m.violation_count || m.violations || 0;
            const b = m.priority_band || m.band || 'N/A';
            
            // Only add if we have valid lat/lng
            if (m.latitude && m.longitude) {
                L.circleMarker([m.latitude, m.longitude], { radius: b === "Critical" ? 8 : 6, color: c, fillColor: c, fillOpacity: .7, weight: 2 })
                 .bindTooltip(`<b>${name}</b><br/>Band: ${b}<br/>Violations: ${v.toLocaleString()}`, { className: "!bg-[#1e293b] !text-[#e2e8f0] !border-[#334155] !text-xs !rounded-lg !px-3 !py-2 !shadow-xl" })
                 .addTo(map);
            }
        });

        if (routeCoords && routeCoords.length > 1) {
            L.polyline(routeCoords, { color: "#22d3ee", weight: 3, opacity: .8, dashArray: "8 6" }).addTo(map);
            routeCoords.forEach((coord, i) => {
                L.marker(coord, { icon: L.divIcon({ html: `<div style="background:${i === 0 ? "#22c55e" : "#3b82f6"};color:#fff;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;border:2px solid #fff;box-shadow:0 0 8px rgba(0,0,0,.4)">${i + 1}</div>`, iconSize: [20, 20], iconAnchor: [10, 10] }) }).addTo(map);
            });
        }
        
        mapInstanceRef.current = map;
        setTimeout(() => map.invalidateSize(), 100);
        return () => { if (mapInstanceRef.current) { mapInstanceRef.current.remove(); mapInstanceRef.current = null; } };
    }, [markers, routeCoords, center, zoom]);

    return <div ref={mapRef} className={`rounded-lg overflow-hidden z-0 ${className}`} style={{ height, minHeight: 200 }} />;
};

export default LeafletMap;
