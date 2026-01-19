import DashboardClient from './DashboardClient';

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
    return <DashboardClient summary={summary} />;
}
