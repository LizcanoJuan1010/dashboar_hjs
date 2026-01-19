import { Card, Title, Text, Metric, Grid, Col } from "@tremor/react";

async function getSummary() {
    try {
        const res = await fetch('http://backend:8000/api/geo/summary', { cache: 'no-store' });
        if (!res.ok) throw new Error('Failed to fetch data');
        return res.json();
    } catch (e) {
        console.error(e);
        return null;
    }
}

export default async function Home() {
    const summary = await getSummary();

    return (
        <main className="p-4 md:p-10 mx-auto max-w-7xl">
            <Title>HJS Campaign Analytics</Title>
            <Text>Real-time data from the Campaign Command Center</Text>

            <Grid numItems={1} numItemsSm={2} numItemsLg={3} className="gap-6 mt-6">
                <Col>
                    <Card decoration="top" decorationColor="indigo">
                        <Text>Total Census</Text>
                        <Metric>{summary ? summary.censo_total.toLocaleString() : '...'}</Metric>
                    </Card>
                </Col>
                <Col>
                    <Card decoration="top" decorationColor="fuchsia">
                        <Text>Total Contacts</Text>
                        <Metric>{summary ? summary.contactos_hjs.toLocaleString() : '...'}</Metric>
                    </Card>
                </Col>
                <Col>
                    <Card decoration="top" decorationColor="teal">
                        <Text>Companies</Text>
                        <Metric>{summary ? summary.empresas_registradas.toLocaleString() : '...'}</Metric>
                    </Card>
                </Col>
            </Grid>

            <Grid numItems={1} numItemsSm={2} className="gap-6 mt-6">
                <Col>
                    <a href="/corporate">
                        <Card className="hover:bg-gray-50 transition-colors cursor-pointer">
                            <Title>🏢 Corporate Analytics</Title>
                            <Text className="mt-2">View Heatmaps, Age Distributions and Employee Stats</Text>
                        </Card>
                    </a>
                </Col>
                <Col>
                    <a href="/territory">
                        <Card className="hover:bg-gray-50 transition-colors cursor-pointer">
                            <Title>🗺️ Territory Command</Title>
                            <Text className="mt-2">Filter by Zone/Puesto and view Campaign Coverage</Text>
                        </Card>
                    </a>
                </Col>
            </Grid>
        </main>
    );
}
