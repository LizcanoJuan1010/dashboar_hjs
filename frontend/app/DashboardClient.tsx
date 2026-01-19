'use client';

import React, { useEffect, useRef, useState } from 'react';
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
import Link from 'next/link';

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

export default function DashboardClient({ summary }: { summary: any }) {
    const [activeRegion, setActiveRegion] = useState('Nacional');
    const [chartData, setChartData] = useState<number[]>([65, 59, 80, 81, 56, 55, 40]);

    // Gradient Setup for Line Chart
    const chartRef = useRef<any>(null);
    const [chartGradient, setChartGradient] = useState<any>(null);

    useEffect(() => {
        const ctx = chartRef.current?.ctx;
        if (ctx) {
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(239, 68, 68, 0.5)');
            gradient.addColorStop(1, 'rgba(239, 68, 68, 0)');
            setChartGradient(gradient);
        }
    }, []);

    const regionsData: any = {
        'Nacional': { label: 'Vista Nacional', data: [65, 59, 80, 81, 56, 55, 40] },
        'Caribe': { label: 'Región Caribe', data: [45, 70, 60, 50, 45, 60, 70] },
        'Antioquia/Santander': { label: 'Antioquia y Santanderes', data: [80, 85, 90, 85, 88, 92, 95] },
        'Pacífico': { label: 'Región Pacífico', data: [30, 35, 40, 38, 45, 40, 50] },
        'Centro': { label: 'Bogotá y Centro', data: [90, 95, 80, 85, 95, 100, 98] },
        'Orinoquía': { label: 'Orinoquía', data: [20, 25, 30, 25, 20, 25, 30] },
        'Amazonía': { label: 'Amazonía', data: [10, 15, 12, 18, 15, 20, 18] }
    };

    const handleRegionClick = (region: string) => {
        setActiveRegion(region);
        setChartData(regionsData[region]?.data || regionsData['Nacional'].data);
    };

    const lineChartData = {
        labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio'],
        datasets: [{
            label: 'Tendencia',
            data: chartData,
            borderColor: '#ef4444',
            backgroundColor: chartGradient || 'rgba(239, 68, 68, 0.5)',
            borderWidth: 2,
            pointBackgroundColor: '#000',
            pointBorderColor: '#ef4444',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            fill: true,
            tension: 0.4
        }]
    };

    const lineOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { display: false }, ticks: { color: '#9ca3af' } },
            y: { border: { display: false }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } }
        }
    };

    return (
        <main className="flex-1 p-4 lg:p-8 max-w-[1600px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6 pb-20">

            {/* Fila Superior: KPIs */}
            <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-4 gap-4 mb-2">
                <div className="glass-panel p-5 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold tracking-wider">Censo Electoral</p>
                        <h3 className="text-2xl font-bold text-white mt-1">{summary?.censo_total?.toLocaleString() || '...'}</h3>
                    </div>
                    <div className="h-10 w-10 rounded-full bg-brand-red/20 flex items-center justify-center text-brand-accent">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
                    </div>
                </div>

                <div className="glass-panel p-5 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold tracking-wider">Contactos HJS</p>
                        <h3 className="text-2xl font-bold text-white mt-1">{summary?.contactos_hjs?.toLocaleString() || '...'}</h3>
                    </div>
                    <div className="text-green-400 text-xs font-mono bg-green-900/20 px-2 py-1 rounded">▲ Activos</div>
                </div>

                <div className="glass-panel p-5 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-gray-400 text-xs uppercase font-bold tracking-wider">Empresas</p>
                        <h3 className="text-2xl font-bold text-white mt-1">{summary?.empresas_registradas?.toLocaleString() || '...'}</h3>
                    </div>
                    <div className="h-2 w-16 bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-brand-accent w-full"></div>
                    </div>
                </div>

                <div className="glass-panel p-5 rounded-xl flex items-center justify-between cursor-pointer hover:bg-brand-red/10 transition-colors">
                    <Link href="/territory" className="w-full h-full flex items-center justify-between">
                        <div>
                            <p className="text-gray-400 text-xs uppercase font-bold tracking-wider">Ver Territorio</p>
                            <h3 className="text-sm font-bold text-brand-neon mt-1">Ir al Mapa ➔</h3>
                        </div>
                        <div className="animate-bounce text-yellow-500">🗺️</div>
                    </Link>
                </div>
            </div>

            {/* Columna Izquierda: Mapa SVG Interactivo */}
            <div className="lg:col-span-4 flex flex-col gap-6">
                <div className="glass-panel rounded-2xl p-1 h-[500px] flex flex-col relative overflow-hidden">
                    <div className="absolute top-4 left-4 z-10">
                        <h3 className="text-white font-bold text-lg">Filtro Geográfico</h3>
                        <p className="text-gray-500 text-xs">Selecciona una región</p>
                    </div>

                    <div className="flex-1 flex items-center justify-center p-4">
                        <svg viewBox="0 0 300 400" className="w-full h-full drop-shadow-2xl">
                            <path d="M80,20 L130,10 L160,30 L150,60 L100,70 L70,50 Z" className={`map-region ${activeRegion === 'Caribe' ? 'active' : ''}`} onClick={() => handleRegionClick('Caribe')}></path>
                            <path d="M80,70 L150,70 L150,130 L100,140 L70,110 Z" className={`map-region ${activeRegion === 'Antioquia/Santander' ? 'active' : ''}`} onClick={() => handleRegionClick('Antioquia/Santander')}></path>
                            <path d="M40,60 L70,80 L70,180 L30,220 L20,100 Z" className={`map-region ${activeRegion === 'Pacífico' ? 'active' : ''}`} onClick={() => handleRegionClick('Pacífico')}></path>
                            <path d="M100,140 L160,130 L160,200 L110,210 Z" className={`map-region ${activeRegion === 'Centro' ? 'active' : ''}`} onClick={() => handleRegionClick('Centro')}></path>
                            <path d="M160,80 L250,80 L280,180 L160,200 Z" className={`map-region ${activeRegion === 'Orinoquía' ? 'active' : ''}`} onClick={() => handleRegionClick('Orinoquía')}></path>
                            <path d="M70,220 L160,200 L280,180 L260,350 L150,390 L80,300 Z" className={`map-region ${activeRegion === 'Amazonía' ? 'active' : ''}`} onClick={() => handleRegionClick('Amazonía')}></path>
                        </svg>
                    </div>

                    <div className="absolute bottom-4 right-4 bg-black/80 backdrop-blur px-3 py-2 rounded border border-gray-800 text-xs text-gray-400">
                        <div className="flex items-center gap-2 mb-1"><span className="w-2 h-2 rounded-full bg-brand-accent"></span> Alto Impacto</div>
                        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#2a0a0a] border border-brand-accent/50"></span> Normal</div>
                    </div>
                </div>

                <div className="glass-panel rounded-2xl p-4 flex-1 overflow-hidden flex flex-col">
                    <h3 className="text-white font-bold text-sm mb-3">Top Municipios (Demo)</h3>
                    <div className="overflow-y-auto pr-2 flex-1">
                        <table className="w-full text-xs text-gray-400">
                            <tbody className="divide-y divide-gray-800">
                                {['Bogotá D.C.', 'Medellín', 'Cali', 'Barranquilla', 'Bucaramanga'].map((city, i) => (
                                    <tr key={city} className="group hover:bg-white/5 cursor-pointer">
                                        <td className="py-2 pl-2 text-white font-medium group-hover:text-red-400">{city}</td>
                                        <td className="py-2 text-right">{35 - (i * 5)}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Columna Derecha: Gráficos */}
            <div className="lg:col-span-8 flex flex-col gap-6">
                <div className="glass-panel p-6 rounded-2xl flex-1 min-h-[350px] flex flex-col relative">
                    <div className="flex justify-between items-start mb-2">
                        <div>
                            <h3 className="text-lg font-bold text-white">Comportamiento Temporal</h3>
                            <p className="text-xs text-gray-500">{regionsData[activeRegion]?.label || 'Vista Nacional'}</p>
                        </div>
                    </div>
                    <div className="relative w-full flex-1">
                        <Line ref={chartRef} data={lineChartData} options={lineOptions} />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[300px]">
                    <div className="glass-panel p-5 rounded-2xl flex flex-col items-center justify-center relative">
                        <h3 className="absolute top-4 left-4 text-sm font-bold text-white">Distribución por Sector</h3>
                        <div className="w-full h-full flex items-center justify-center pt-6">
                            <Doughnut
                                data={{
                                    labels: ['Comercio', 'Servicios', 'Industria'],
                                    datasets: [{
                                        data: [55, 30, 15],
                                        backgroundColor: ['#ef4444', '#7f1d1d', '#1a0505'],
                                        borderWidth: 0,
                                    }]
                                }}
                                options={{ plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, color: '#9ca3af' } } } }}
                            />
                        </div>
                    </div>
                    <div className="glass-panel p-5 rounded-2xl flex flex-col justify-center relative">
                        <h3 className="absolute top-4 left-4 text-sm font-bold text-white">Ranking de Rendimiento</h3>
                        <div className="w-full h-full flex items-center justify-center pt-6">
                            <Bar
                                data={{
                                    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                                    datasets: [{
                                        label: 'KPI',
                                        data: [75, 60, 80, 95],
                                        backgroundColor: '#ef4444',
                                        borderRadius: 4
                                    }]
                                }}
                                options={{
                                    maintainAspectRatio: false,
                                    indexAxis: 'y',
                                    plugins: { legend: { display: false } },
                                    scales: { x: { display: false }, y: { grid: { display: false }, ticks: { color: '#9ca3af' } } }
                                }}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
