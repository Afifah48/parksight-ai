import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import TopNavBar from './components/TopNavBar';
import SideNavBar from './components/SideNavBar';

import Dashboard from './pages/Dashboard';
import Intelligence from './pages/Intelligence';
import Operations from './pages/Operations';
import EmergingThreats from './pages/EmergingThreats';
import VehicleIntel from './pages/VehicleIntel';
import Planning from './pages/Planning';
import Simulator from './pages/Simulator';

function App() {
  return (
    <div className="flex h-screen w-full bg-bg">
      <SideNavBar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopNavBar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/intelligence" element={<Intelligence />} />
          <Route path="/operations" element={<Operations />} />
          <Route path="/analytics" element={<EmergingThreats />} />
          <Route path="/vehicle-intel" element={<VehicleIntel />} />
          <Route path="/planning" element={<Planning />} />
          <Route path="/simulator" element={<Simulator />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
