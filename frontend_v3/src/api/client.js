import axios from 'axios';

const api = axios.create({
  baseURL: 'https://parksight-ai.onrender.com/api',
});

export const fetchKpis = async () => (await api.get('/kpis')).data;
export const fetchHotspots = async (station = null, band = null) => 
  (await api.get('/hotspots', { params: { station, band } })).data;
export const fetchEmerging = async () => (await api.get('/emerging')).data;
export const fetchOffenders = async () => (await api.get('/offenders')).data;
export const fetchRecommendations = async (station = null) => 
  (await api.get('/recommendations', { params: { station } })).data;
export const fetchRoutes = async (station = null) => 
  (await api.get('/routes', { params: { station } })).data;
export const fetchRoi = async () => (await api.get('/roi')).data;

export default api;
