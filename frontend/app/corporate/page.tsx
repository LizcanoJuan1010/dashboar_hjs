"use client";
import { useEffect, useState } from 'react';
import { Card, Title, BarChart, DonutChart, Text, Grid, Col, Flex, Metric } from "@tremor/react";

// Types
type HeatmapData = {
    tipo_empresa: string;
    nivel_educativo: string;
    total: number;
};

type AgeData = {
    rango_edad: string;
    sexo: string;
    total: number;
};

export default function CorporateDashboard() {
    const [heatmapData, setHeatmapData] = useState<HeatmapData[]>([]);
    const [ageData, setAgeData] = useState<AgeData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [hmRes, ageRes] = await Promise.all([
                    fetch('http://localhost:8000/api/analytics/company-heatmap'),
                    fetch('http://localhost:8000/api/analytics/age-distribution')
                ]);

                const hm = await hmRes.json();
                const age = await ageRes.json();

                setHeatmapData(hm);
                setAgeData(age);
            } catch (error) {
                console.error("Failed to fetch corporate analytics", error);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    if (loading) return <Text>Loading Analytics...</Text>;

    // Process Data for Charts
    const ageChartData = ageData.reduce((acc: any[], curr) => {
        const existing = acc.find(item => item.rango_edad === curr.rango_edad);
        if (existing) {
            existing[curr.sexo || 'Desconocido'] = curr.total;
        } else {
            acc.push({
                rango_edad: curr.rango_edad,
                [curr.sexo || 'Desconocido']: curr.total
            });
        }
        return acc;
    }, []);

    return (
        <main className="p-4 md:p-10 mx-auto max-w-7xl">
            <Title>Corporate Analytics (Empresas)</Title>

            <Grid numItems={1} numItemsLg={2} className="gap-6 mt-6">

                {/* Age Distribution */}
                <Col>
                    <Card>
                        <Title>Age Distribution by Gender</Title>
                        <BarChart
                            className="mt-6"
                            data={ageChartData}
                            index="rango_edad"
                            categories={["M", "F", "Desconocido"]}
                            colors={["blue", "pink", "gray"]}
                            yAxisWidth={48}
                        />
                    </Card>
                </Col>

                {/* Placeholder for Heatmap (Tremor doesn't have native Heatmap yet, using Table/Grid) */}
                <Col>
                    <Card>
                        <Title>Education vs Company Type</Title>
                        <div className="mt-4 h-80 overflow-y-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs uppercase bg-gray-100 dark:bg-gray-700">
                                    <tr>
                                        <th className="px-4 py-2">Company Type</th>
                                        <th className="px-4 py-2">Education</th>
                                        <th className="px-4 py-2">Employees</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {heatmapData.map((row, idx) => (
                                        <tr key={idx} className="border-b dark:border-gray-700">
                                            <td className="px-4 py-2 font-medium">{row.tipo_empresa}</td>
                                            <td className="px-4 py-2">{row.nivel_educativo}</td>
                                            <td className="px-4 py-2">{row.total}</td>
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
