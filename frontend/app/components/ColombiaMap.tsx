import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3-geo';
import { feature } from 'topojson-client'; // Note: using raw geojson, no topojson needed, but d3 handles it.

interface ColombiaMapProps {
    onRegionClick: (regionName: string, regionId: string) => void;
    activeRegionId?: string; // We use ID (Divipole code) for selection
}

export default function ColombiaMap({ onRegionClick, activeRegionId }: ColombiaMapProps) {
    const [geoData, setGeoData] = useState<any>(null);
    const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);

    useEffect(() => {
        fetch('/maps/colombia.json')
            .then(res => res.json())
            .then(data => setGeoData(data))
            .catch(err => console.error("Failed to load map data", err));
    }, []);

    if (!geoData) return <div className="flex items-center justify-center h-full text-brand-accent animate-pulse">Cargando mapa...</div>;

    // Projection Setup
    // Center of Colombia roughly: -74, 4.5. Scale adjusted for 300x400 container.
    const projection = d3.geoMercator()
        .center([-74.2, 4.6])
        .scale(1800) // Adjust scale to fit container
        .translate([150, 200]); // Center in specific SVG dimensions (300 wide, 400 high)

    const pathGenerator = d3.geoPath().projection(projection);

    return (
        <div className="w-full h-full relative group">
            <svg viewBox="0 0 300 400" className="w-full h-full drop-shadow-2xl">
                <defs>
                    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>

                {geoData.features.map((feature: any) => {
                    const id = feature.id || feature.properties.DPTO;
                    const name = feature.properties.NOMBRE_DPT;
                    const isActive = activeRegionId === id || activeRegionId === name;
                    const isHovered = hoveredRegion === id;

                    return (
                        <path
                            key={id}
                            d={pathGenerator(feature) || ''}
                            className={`
                                cursor-pointer transition-all duration-300 stroke-[0.5]
                                ${isActive
                                    ? 'fill-brand-accent stroke-white stroke-2 active-region-glow'
                                    : 'fill-white/10 stroke-white/20 hover:fill-brand-accent/60'
                                }
                            `}
                            style={{
                                filter: isActive || isHovered ? 'url(#glow)' : 'none'
                            }}
                            onMouseEnter={() => setHoveredRegion(id)}
                            onMouseLeave={() => setHoveredRegion(null)}
                            onClick={() => onRegionClick(name, id)}
                        >
                            <title>{name}</title>
                        </path>
                    );
                })}
            </svg>

            {/* Tooltip Effect for Hovered Region Name */}
            {hoveredRegion && (
                <div className="absolute bottom-4 left-4 pointer-events-none bg-black/80 backdrop-blur px-3 py-1 rounded border border-brand-accent/50 text-white text-xs font-bold tracking-wider">
                    {geoData.features.find((f: any) => (f.id || f.properties.DPTO) === hoveredRegion)?.properties.NOMBRE_DPT}
                </div>
            )}
        </div>
    );
}
