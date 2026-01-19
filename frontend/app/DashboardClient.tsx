'use client';

import React, { useEffect, useState, useMemo } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ArcElement
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import ColombiaMap from './components/ColombiaMap';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ArcElement
);

const normalizeText = (text: string) => {
    if (!text) return '';
    return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().trim();
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DashboardClient({ summary: initialSummary }: { summary: any }) {
    // Region state: code (DPTO) and name
    const [activeRegionCode, setActiveRegionCode] = useState<string | null>(null);
    const [activeRegionName, setActiveRegionName] = useState('Nacional');
    const [loading, setLoading] = useState(true);

    // Dynamic summary (updates when region changes)
    const [summary, setSummary] = useState(initialSummary);

    // Data states
    const [educationData, setEducationData] = useState<any[]>([]);
    const [sexData, setSexData] = useState<any[]>([]);
    const [topCompaniesData, setTopCompaniesData] = useState<any[]>([]);
    const [puestosData, setPuestosData] = useState<any[]>([]);
    const [leaderData, setLeaderData] = useState<any[]>([]);
    const [timelineData, setTimelineData] = useState<any[]>([]);
    const [mesasData, setMesasData] = useState<any[]>([]);
    const [coverageData, setCoverageData] = useState<any[]>([]);
    const [verifiedLeadersData, setVerifiedLeadersData] = useState<any[]>([]);
    const [empresasByDeptData, setEmpresasByDeptData] = useState<any[]>([]);

    // New Data States
    const [contactData, setContactData] = useState<any[]>([]);
    const [birthdayData, setBirthdayData] = useState<any[]>([]);

    // Drill-down states
    const [municipiosData, setMunicipiosData] = useState<any[]>([]);
    const [puestosDrillData, setPuestosDrillData] = useState<any[]>([]);
    const [selectedMunicipio, setSelectedMunicipio] = useState<string | null>(null);

    const [mounted, setMounted] = useState(false);
    useEffect(() => { setMounted(true); }, []);
    const fmt = (n: number) => mounted ? (n?.toLocaleString('es-CO') || '0') : '...';

    // Initial data fetch
    useEffect(() => {
        const fetchAll = async () => {
            try {
                const endpoints = [
                    `${API_BASE}/api/analytics/education-level`,
                    `${API_BASE}/api/analytics/sex-distribution`,
                    `${API_BASE}/api/analytics/top-companies`,
                    `${API_BASE}/api/analytics/puestos-demographics`,
                    `${API_BASE}/api/analytics/leader-efficiency`,
                    `${API_BASE}/api/analytics/company-timeline`,
                    `${API_BASE}/api/analytics/mesas-by-dept`,
                    `${API_BASE}/api/analytics/coverage-by-puesto?limit=200`,
                    `${API_BASE}/api/analytics/verified-leaders`,
                    `${API_BASE}/api/analytics/empresas-by-dept`,
                    `${API_BASE}/api/analytics/contact-info?limit=100`, // New
                    `${API_BASE}/api/analytics/upcoming-birthdays?limit=100` // New
                ];

                const results = await Promise.all(
                    endpoints.map(url => fetch(url).then(r => r.ok ? r.json() : []).catch(() => []))
                );

                setEducationData(results[0]);
                setSexData(results[1]);
                setTopCompaniesData(results[2]);
                setPuestosData(results[3]);
                setLeaderData(results[4]);
                setTimelineData(results[5]);
                setMesasData(results[6]);
                setCoverageData(results[7]);
                setVerifiedLeadersData(results[8]);
                setEmpresasByDeptData(results[9]);
                setContactData(results[10]);
                setBirthdayData(results[11]);
            } catch (error) {
                console.error("Error fetching analytics:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchAll();
    }, []);

    // Fetch filtered data when department changes
    useEffect(() => {
        const fetchDeptData = async () => {
            if (activeRegionCode) {
                try {
                    const [summaryRes, mesasRes, empresasRes, municipiosRes] = await Promise.all([
                        fetch(`${API_BASE}/api/geo/summary?cod_dept=${activeRegionCode}`),
                        fetch(`${API_BASE}/api/analytics/mesas-by-dept?cod_dept=${activeRegionCode}`),
                        fetch(`${API_BASE}/api/analytics/empresas-by-dept?cod_dept=${activeRegionCode}`),
                        fetch(`${API_BASE}/api/analytics/municipios-by-dept?cod_dept=${activeRegionCode}`)
                    ]);

                    if (summaryRes.ok) setSummary(await summaryRes.json());
                    if (mesasRes.ok) setMesasData(await mesasRes.json());
                    if (empresasRes.ok) setEmpresasByDeptData(await empresasRes.json());
                    if (municipiosRes.ok) setMunicipiosData(await municipiosRes.json());
                    setPuestosDrillData([]);
                    setSelectedMunicipio(null);
                } catch (error) {
                    console.error("Error fetching dept data:", error);
                }
            } else {
                // Reset to national
                setSummary(initialSummary);
                setMunicipiosData([]);
                setPuestosDrillData([]);
                setSelectedMunicipio(null);
                // Refetch all data
                const [mesasRes, empresasRes] = await Promise.all([
                    fetch(`${API_BASE}/api/analytics/mesas-by-dept`),
                    fetch(`${API_BASE}/api/analytics/empresas-by-dept`)
                ]);
                if (mesasRes.ok) setMesasData(await mesasRes.json());
                if (empresasRes.ok) setEmpresasByDeptData(await empresasRes.json());
            }
        };
        fetchDeptData();
    }, [activeRegionCode, initialSummary]);

    // Fetch puestos when municipio selected
    useEffect(() => {
        const fetchPuestos = async () => {
            if (selectedMunicipio) {
                try {
                    const res = await fetch(`${API_BASE}/api/analytics/puestos-by-muni?cod_muni=${selectedMunicipio}&cod_dept=${activeRegionCode}`);
                    if (res.ok) setPuestosDrillData(await res.json());
                } catch (error) {
                    console.error("Error fetching puestos:", error);
                }
            } else {
                setPuestosDrillData([]);
            }
        };
        fetchPuestos();
    }, [selectedMunicipio]);

    // Handle region click from map
    const handleRegionClick = (name: string, code: string) => {
        if (activeRegionCode === code) {
            // Click same region = deselect
            setActiveRegionCode(null);
            setActiveRegionName('Nacional');
        } else {
            setActiveRegionCode(code);
            setActiveRegionName(name);
        }
    };

    // Filter data by cod_departamento
    const filteredStats = useMemo(() => {
        const filterByDept = (item: any) => {
            if (!activeRegionCode) return true;
            return item.cod_departamento === activeRegionCode;
        };

        const eduMap = new Map<string, number>();
        educationData.filter(filterByDept).forEach(e => {
            const key = e.nivel_educativo || 'No Registrado';
            eduMap.set(key, (eduMap.get(key) || 0) + (e.total_personas || 0));
        });
        const edu = { labels: Array.from(eduMap.keys()), data: Array.from(eduMap.values()) };

        const sexMap = new Map<string, number>();
        sexData.filter(filterByDept).forEach(s => {
            const key = s.sexo === 'M' ? 'Masculino' : s.sexo === 'F' ? 'Femenino' : 'Otro';
            sexMap.set(key, (sexMap.get(key) || 0) + (s.total || 0));
        });
        const sex = { labels: Array.from(sexMap.keys()), data: Array.from(sexMap.values()) };

        const topComp = topCompaniesData.filter(filterByDept).slice(0, 10);

        const topPuestos = puestosData.filter(filterByDept).slice(0, 10);

        const leaders = leaderData.filter(filterByDept).slice(0, 10);

        // Timeline data - Keep filter logic if needed, but we are removing the chart
        const timeMap = new Map<string, number>();
        timelineData.filter(filterByDept).forEach(t => {
            const year = t.anio;
            if (year) timeMap.set(year, (timeMap.get(year) || 0) + (t.total_empresas || 0));
        });
        const sortedYears = Array.from(timeMap.keys()).sort();
        const timeline = { labels: sortedYears, data: sortedYears.map(y => timeMap.get(y) || 0) };


        const coverage = coverageData.filter(filterByDept).slice(0, 10);

        return { edu, sex, topComp, topPuestos, leaders, timeline, coverage };
    }, [activeRegionCode, educationData, sexData, topCompaniesData, puestosData, leaderData, timelineData, coverageData]);

    const chartColors = { primary: '#ef4444', secondary: '#7f1d1d', text: '#9ca3af' };

    const barEducationData = {
        labels: filteredStats.edu.labels.slice(0, 8),
        datasets: [{
            label: 'Personas',
            data: filteredStats.edu.data.slice(0, 8),
            backgroundColor: chartColors.primary,
            borderRadius: 4
        }]
    };

    const pieSexData = {
        labels: filteredStats.sex.labels,
        datasets: [{
            data: filteredStats.sex.data,
            backgroundColor: [chartColors.primary, chartColors.secondary, '#450a0a'],
            borderWidth: 0
        }]
    };

    // Mesas chart - show municipalities if department selected, else show departments
    const barMesasData = {
        labels: activeRegionCode
            ? municipiosData.slice(0, 10).map(d => d.municipio?.substring(0, 12) || 'N/A')
            : mesasData.slice(0, 10).map(d => d.departamento?.substring(0, 12) || 'N/A'),
        datasets: [{
            label: activeRegionCode ? 'Mesas por Municipio' : 'Mesas por Depto',
            data: activeRegionCode
                ? municipiosData.slice(0, 10).map(d => d.total_mesas)
                : mesasData.slice(0, 10).map(d => d.total_mesas),
            backgroundColor: chartColors.primary,
            borderRadius: 4
        }]
    };

    // Empresas chart
    const barEmpresasData = {
        labels: empresasByDeptData.slice(0, 10).map(d => d.departamento?.substring(0, 12) || 'N/A'),
        datasets: [{
            label: 'Total Empresas',
            data: empresasByDeptData.slice(0, 10).map(d => d.total_empresas),
            backgroundColor: chartColors.primary,
            borderRadius: 4
        }]
    };

    const commonOptions: any = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { display: false }, ticks: { color: chartColors.text, font: { size: 10 } } },
            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: chartColors.text, font: { size: 10 } } }
        }
    };

    if (loading) {
        return (
            <main className="flex-1 flex items-center justify-center min-h-screen">
                <div className="text-brand-accent text-xl animate-pulse">Cargando Dashboard...</div>
            </main>
        );
    }

    return (
        <main className="flex-1 p-4 lg:p-6 max-w-[1600px] mx-auto w-full space-y-6 pb-20">

            {/* KPI Row - Now uses dynamic summary */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold">Censo</p>
                        <h3 className="text-lg font-bold text-white">{fmt(summary?.censo_total)}</h3>
                    </div>
                    <span className="text-2xl">👤</span>
                </div>
                <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold">Contactos</p>
                        <h3 className="text-lg font-bold text-white">{fmt(summary?.contactos_hjs)}</h3>
                    </div>
                    <span className="text-2xl">📞</span>
                </div>
                <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold">Empresas</p>
                        <h3 className="text-lg font-bold text-white">{fmt(summary?.empresas_registradas)}</h3>
                    </div>
                    <span className="text-2xl">🏢</span>
                </div>
                <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold">Empleados</p>
                        <h3 className="text-lg font-bold text-white">{fmt(summary?.empleados_registrados || 0)}</h3>
                    </div>
                    <span className="text-2xl">👷</span>
                </div>
                <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold">Emails</p>
                        <h3 className="text-lg font-bold text-white">{fmt(summary?.total_emails || 0)}</h3>
                    </div>
                    <span className="text-lg">📧</span>
                </div>
                <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold">Celulares</p>
                        <h3 className="text-lg font-bold text-white">{fmt(summary?.total_celulares || 0)}</h3>
                    </div>
                    <span className="text-lg">📱</span>
                </div>
            </div>

            {/* Main Grid */}
            <div className="grid lg:grid-cols-12 gap-5">

                {/* Left Column: Map + Tables */}
                <div className="lg:col-span-4 space-y-5">
                    {/* Map */}
                    <div className="glass-panel rounded-2xl p-4">
                        <h3 className="text-white font-bold text-sm mb-2">Mapa de Colombia</h3>
                        <div className="h-[350px]">
                            <ColombiaMap
                                onRegionClick={handleRegionClick}
                                activeRegionId={activeRegionCode || ''}
                            />
                        </div>
                    </div>

                    {/* Drill-down: Municipios */}
                    {activeRegionCode && municipiosData.length > 0 && (
                        <div className="glass-panel rounded-2xl p-4">
                            <h3 className="text-white font-bold text-sm mb-3">Municipios en {activeRegionName}</h3>
                            <div className="overflow-auto max-h-[200px]">
                                <table className="w-full text-xs text-gray-400">
                                    <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#0a0a0a]">
                                        <tr><th className="pb-2 text-left">Municipio</th><th className="pb-2 text-right">Mesas</th></tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                        {municipiosData.map((m, i) => (
                                            <tr
                                                key={i}
                                                className={`hover:bg-white/10 cursor-pointer ${selectedMunicipio === m.cod_municipio ? 'bg-brand-accent/20' : ''}`}
                                                onClick={() => setSelectedMunicipio(selectedMunicipio === m.cod_municipio ? null : m.cod_municipio)}
                                            >
                                                <td className="py-1 text-white">{m.municipio}</td>
                                                <td className="py-1 text-right font-bold text-brand-accent">{fmt(m.total_mesas)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Drill-down: Puestos */}
                    {selectedMunicipio && puestosDrillData.length > 0 && (
                        <div className="glass-panel rounded-2xl p-4">
                            <h3 className="text-white font-bold text-sm mb-3">Puestos de Votación</h3>
                            <div className="overflow-auto max-h-[200px]">
                                <table className="w-full text-xs text-gray-400">
                                    <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#0a0a0a]">
                                        <tr><th className="pb-2 text-left">Puesto</th><th className="pb-2 text-right">Mesas</th></tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                        {puestosDrillData.map((p, i) => (
                                            <tr key={i} className="hover:bg-white/5">
                                                <td className="py-1 text-white truncate max-w-[150px]" title={p.direccion}>{p.puesto}</td>
                                                <td className="py-1 text-right font-bold text-brand-accent">{fmt(p.total_mesas)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Puestos Demographics */}
                    <div className="glass-panel rounded-2xl p-4">
                        <h3 className="text-white font-bold text-sm mb-3">Demografía Puestos</h3>
                        <div className="overflow-auto max-h-[200px]">
                            <table className="w-full text-xs text-gray-400">
                                <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#0a0a0a]">
                                    <tr><th className="pb-2 text-left">Puesto</th><th className="pb-2 text-right">H</th><th className="pb-2 text-right">M</th><th className="pb-2 text-right">Total</th></tr>
                                </thead>
                                <tbody className="divide-y divide-gray-800">
                                    {filteredStats.topPuestos.map((p, i) => (
                                        <tr key={i} className="hover:bg-white/5">
                                            <td className="py-1 text-white truncate max-w-[80px]">{p.puesto}</td>
                                            <td className="py-1 text-right text-blue-400">{fmt(p.hombres)}</td>
                                            <td className="py-1 text-right text-pink-400">{fmt(p.mujeres)}</td>
                                            <td className="py-1 text-right font-bold">{fmt(p.total_general)}</td>
                                        </tr>
                                    ))}
                                    {filteredStats.topPuestos.length === 0 && <tr><td colSpan={4} className="py-3 text-center">Sin datos</td></tr>}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Coverage Table */}
                    <div className="glass-panel rounded-2xl p-4">
                        <h3 className="text-white font-bold text-sm mb-3">Cobertura HJS (Top 10)</h3>
                        <div className="overflow-auto max-h-[200px]">
                            <table className="w-full text-xs text-gray-400">
                                <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#0a0a0a]">
                                    <tr><th className="pb-2 text-left">Puesto</th><th className="pb-2 text-right">Censo</th><th className="pb-2 text-right">Cont.</th><th className="pb-2 text-right">%</th></tr>
                                </thead>
                                <tbody className="divide-y divide-gray-800">
                                    {filteredStats.coverage.map((c, i) => (
                                        <tr key={i} className="hover:bg-white/5">
                                            <td className="py-1 text-white truncate max-w-[80px]">{c.puesto}</td>
                                            <td className="py-1 text-right">{fmt(c.censo)}</td>
                                            <td className="py-1 text-right">{fmt(c.contactos)}</td>
                                            <td className="py-1 text-right font-bold text-brand-accent">{c.cobertura_pct}%</td>
                                        </tr>
                                    ))}
                                    {filteredStats.coverage.length === 0 && <tr><td colSpan={4} className="py-3 text-center">Sin datos</td></tr>}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Right Column: Charts */}
                <div className="lg:col-span-8 space-y-5">

                    {/* Row 1: Empresas + Mesas */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div className="glass-panel p-4 rounded-2xl">
                            <h3 className="text-white font-bold text-sm mb-3">Empresas por Departamento</h3>
                            <div className="h-[200px]"><Bar data={barEmpresasData} options={{ ...commonOptions, indexAxis: 'y' as const }} /></div>
                        </div>
                        <div className="glass-panel p-4 rounded-2xl">
                            <h3 className="text-white font-bold text-sm mb-3">
                                {activeRegionCode ? `Mesas por Municipio (${activeRegionName})` : 'Mesas por Departamento'}
                            </h3>
                            <div className="h-[200px]"><Bar data={barMesasData} options={{ ...commonOptions, indexAxis: 'y' as const }} /></div>
                        </div>
                    </div>

                    {/* Row 2: Contact List + Birthdays (Replacing Timeline) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        {/* Contact Info Table */}
                        <div className="glass-panel p-4 rounded-2xl">
                            <h3 className="text-white font-bold text-sm mb-3">Información de Contacto (Reciente)</h3>
                            <div className="overflow-auto max-h-[250px]">
                                <table className="w-full text-xs text-gray-400">
                                    <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#0a0a0a]">
                                        <tr>
                                            <th className="pb-2 text-left">Documento</th>
                                            <th className="pb-2 text-left">Nombre</th>
                                            <th className="pb-2 text-left">Celular</th>
                                            <th className="pb-2 text-left">Email</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                        {contactData.map((c, i) => (
                                            <tr key={i} className="hover:bg-white/5">
                                                <td className="py-1 text-white">{c.documento}</td>
                                                <td className="py-1 text-white truncate max-w-[120px]" title={c.nombre_completo}>{c.nombre_completo}</td>
                                                <td className="py-1 text-gray-300">{c.celular || '-'}</td>
                                                <td className="py-1 text-gray-300 truncate max-w-[150px]" title={c.email}>{c.email || '-'}</td>
                                            </tr>
                                        ))}
                                        {contactData.length === 0 && <tr><td colSpan={4} className="py-3 text-center">Cargando...</td></tr>}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Upcoming Birthdays Table */}
                        <div className="glass-panel p-4 rounded-2xl">
                            <h3 className="text-white font-bold text-sm mb-3">Próximos Cumpleaños</h3>
                            <div className="overflow-auto max-h-[250px]">
                                <table className="w-full text-xs text-gray-400">
                                    <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#0a0a0a]">
                                        <tr>
                                            <th className="pb-2 text-left">Nombre</th>
                                            <th className="pb-2 text-left">Fecha</th>
                                            <th className="pb-2 text-left">Contacto</th>
                                            <th className="pb-2 text-right">Días</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                        {birthdayData.map((b, i) => (
                                            <tr key={i} className="hover:bg-white/5">
                                                <td className="py-1 text-white truncate max-w-[120px]" title={b.nombre_completo}>{b.nombre_completo}</td>
                                                <td className="py-1 text-gray-300">{new Date(b.fecha_nacimiento).toLocaleDateString('es-CO', { day: 'numeric', month: 'short' })}</td>
                                                <td className="py-1 text-gray-300 truncate max-w-[100px]" title={`${b.celular || ''} ${b.email || ''}`}>
                                                    {b.email || b.celular || '-'}
                                                </td>
                                                <td className="py-1 text-right font-bold text-brand-accent">{b.days_until_birthday}</td>
                                            </tr>
                                        ))}
                                        {birthdayData.length === 0 && <tr><td colSpan={4} className="py-3 text-center">Cargando...</td></tr>}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Row 3: Sex + Education */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                        <div className="glass-panel p-4 rounded-2xl">
                            <h3 className="text-white font-bold text-sm mb-3">Sexo</h3>
                            <div className="h-[180px] flex items-center justify-center">
                                <Doughnut data={pieSexData} options={{ plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, color: chartColors.text } } } }} />
                            </div>
                        </div>
                        <div className="glass-panel p-4 rounded-2xl col-span-2">
                            <h3 className="text-white font-bold text-sm mb-3">Nivel Educativo</h3>
                            <div className="h-[180px]"><Bar data={barEducationData} options={commonOptions} /></div>
                        </div>
                    </div>

                    {/* Row 4: Leaders + Companies */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div className="glass-panel p-4 rounded-2xl">
                            <h3 className="text-white font-bold text-sm mb-3">Líderes: Recursos vs Meta</h3>
                            <div className="overflow-auto max-h-[200px]">
                                <table className="w-full text-xs text-gray-400">
                                    <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#0a0a0a]">
                                        <tr><th className="pb-2 text-left">Líder</th><th className="pb-2 text-right">Meta</th><th className="pb-2 text-right">Recursos</th></tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                        {filteredStats.leaders.map((l, i) => (
                                            <tr key={i} className="hover:bg-white/5">
                                                <td className="py-1 text-white truncate max-w-[100px]">{l.lider}</td>
                                                <td className="py-1 text-right">{fmt(l.meta_votos)}</td>
                                                <td className="py-1 text-right font-bold text-brand-accent">{fmt(l.total_recursos)}</td>
                                            </tr>
                                        ))}
                                        {filteredStats.leaders.length === 0 && <tr><td colSpan={3} className="py-3 text-center">Sin datos</td></tr>}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div className="glass-panel p-4 rounded-2xl">
                            <h3 className="text-white font-bold text-sm mb-3">Top Empresas</h3>
                            <div className="overflow-auto max-h-[200px]">
                                <table className="w-full text-xs text-gray-400">
                                    <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#0a0a0a]">
                                        <tr><th className="pb-2 text-left">Empresa</th><th className="pb-2 text-right">Empleados</th></tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                        {filteredStats.topComp.map((c, i) => (
                                            <tr key={i} className="hover:bg-white/5">
                                                <td className="py-1 text-white truncate max-w-[150px]">{c.empresa}</td>
                                                <td className="py-1 text-right font-bold text-brand-accent">{fmt(c.total_empleados)}</td>
                                            </tr>
                                        ))}
                                        {filteredStats.topComp.length === 0 && <tr><td colSpan={2} className="py-3 text-center">Sin datos</td></tr>}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
