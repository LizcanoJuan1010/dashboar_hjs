"use client";
import { useEffect, useState } from 'react';
import { Card, Title, Text, Grid, Col, BarChart } from "@tremor/react";

// Types
type CoverageData = {
    nom_municipio: string;
    nombre_puesto: string;
    censo: number;
    contactos: number;
    cobertura_pct: number;
};

type LeaderData = {
    comuna: string;
    total_lideres: number;
    lideres_verificados: number;
    meta_total_votos: number;
}

export default function TerritoryDashboard() {
    const [coverageData, setCoverageData] = useState<CoverageData[]>([]);
    const [leaderData, setLeaderData] = useState<LeaderData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [covRes, leadRes] = await Promise.all([
                    fetch('http://localhost:8000/api/analytics/coverage-by-puesto?limit=50'),
                    fetch('http://localhost:8000/api/analytics/verified-leaders')
                ]);

                setCoverageData(await covRes.json());
                setLeaderData(await leadRes.json());
            } catch (error) {
                console.error("Failed to fetch territory analytics", error);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    if (loading) return <Text>Loading Analytics...</Text>;

    return (
        <main className="p-4 md:p-10 mx-auto max-w-7xl">
            <Title>Territory Command (Censo & Campaña)</Title>

            <Grid numItems={1} className="gap-6 mt-6">

                {/* Coverage Chart */}
                <Col>
                    <Card>
                        <Title>Top 50 Puestos by Coverage %</Title>
                        <BarChart
                            className="mt-6 h-80"
                            data={coverageData}
                            index="nombre_puesto"
                            categories={["cobertura_pct"]}
                            colors={["emerald"]}
                            yAxisWidth={48}
                            valueFormatter={(number) => `${number}%`}
                        />
                    </Card>
                </Col>

                {/* Leaders Stats */}
                <Col>
                    <Card>
                        <Title>Leaders Performance by Zone (Comuna)</Title>
                        <div className="mt-4 h-80 overflow-y-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs uppercase bg-gray-100 dark:bg-gray-700">
                                    <tr>
                                        <th className="px-4 py-2">Zone / Comuna</th>
                                        <th className="px-4 py-2">Total Leaders</th>
                                        <th className="px-4 py-2">Verified</th>
                                        <th className="px-4 py-2">Vote Goal</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {leaderData.map((row, idx) => (
                                        <tr key={idx} className="border-b dark:border-gray-700">
                                            <td className="px-4 py-2 font-medium">{row.comuna}</td>
                                            <td className="px-4 py-2">{row.total_lideres}</td>
                                            <td className="px-4 py-2">{row.lideres_verificados}</td>
                                            <td className="px-4 py-2">{row.meta_total_votos}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </Card>
                </Col>

            </Grid>
        </main>
    );
}
