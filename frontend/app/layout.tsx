import './globals.css'
import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'Dashboard EDA - Colombia Analytics',
  description: 'Premium Analytical Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={`${inter.variable} ${mono.variable} font-sans min-h-screen flex flex-col antialiased bg-black text-gray-200 selection:bg-red-500 selection:text-white`}>

        {/* Navbar */}
        <nav className="h-16 border-b border-brand-red/30 bg-brand-bg/80 backdrop-blur-md sticky top-0 z-50 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-brand-accent flex items-center justify-center text-white font-bold shadow-[0_0_15px_rgba(239,68,68,0.5)]">
              CO
            </div>
            <h1 className="text-xl font-bold tracking-wider text-white">COLOMBIA <span className="text-brand-accent font-mono">ANALYTICS</span></h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden md:flex px-3 py-1 rounded-full border border-brand-accent/30 bg-red-950/20 text-red-200 text-xs uppercase tracking-widest animate-pulse-slow">
              Vista General
            </span>
            <div className="w-8 h-8 rounded-full bg-gray-800 border border-gray-700"></div>
          </div>
        </nav>

        {children}

        {/* Footer */}
        <footer className="border-t border-gray-900 bg-black py-8 text-center mt-auto">
          <p className="text-gray-600 text-xs font-mono">Desarrollado para Análisis de Datos Colombia &copy; 2026</p>
        </footer>
      </body>
    </html>
  )
}
