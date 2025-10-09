// In mlbb-analytics-frontend/app/page.tsx
import Link from 'next/link';
import Image from 'next/image';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Swords, Telescope, Lightbulb } from 'lucide-react';

export default function HomePage() {
  return (
    <>
      <main className="container mx-auto p-4 md:p-8">
        {/* Hero Section */}
        <section className="text-center py-12">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
            MLBB Analytics Dashboard
          </h1>
          <p className="mt-4 text-lg text-gray-400 max-w-2xl mx-auto">
            A modern, full-stack web application providing in-depth statistical insights into professional Mobile Legends esports.
          </p>
        </section>

        {/* Introduction and Quote Section */}
        <section className="mb-12">
            <Card className="bg-gray-800 border-gray-700">
                <CardHeader>
                    <CardTitle className="text-white">Introduction</CardTitle>
                </CardHeader>
                <CardContent>
                    {/* Authentic Introduction from Streamlit */}
                    <p className="text-gray-400 mb-6">
                        Welcome to the MLBB Professional Scene Meta Analyzer. This dashboard offers insights into the hero meta of various professional Mobile Legends: Bang Bang tournaments. By analyzing picks, bans, and win rates, we can uncover trends and understand the strategic priorities of top-tier teams. All data is sourced from the Liquipedia API. This is a Proof-of-Concept (PoC) and is still under development.
                    </p>
                    {/* Authentic Quote from Streamlit */}
                    <blockquote className="border-l-4 border-blue-500 pl-4 py-2 bg-gray-800/50">
                        <div className="flex items-center gap-3">
                            <Lightbulb className="w-5 h-5 text-blue-400" />
                            <p className="italic text-gray-300">
                                "To know your enemy, you must become your enemy." - Sun Tzu, The Art of War
                            </p>
                        </div>
                    </blockquote>
                </CardContent>
            </Card>
        </section>

        {/* Features Section */}
        <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link href="/statistics">
            <Card className="bg-gray-800 border-gray-700 hover:bg-gray-700/50 hover:border-blue-500 transition-all cursor-pointer h-full">
              <CardHeader className="flex flex-row items-center gap-4 pb-2">
                <BarChart3 className="w-8 h-8 text-blue-400" />
                <CardTitle className="text-white">Statistics Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Explore detailed hero stats like picks, bans, win rates, and presence across professional tournaments.
                </CardDescription>
              </CardContent>
            </Card>
          </Link>
          
          <Card className="bg-gray-800 border-gray-700 h-full opacity-50">
             <CardHeader className="flex flex-row items-center gap-4 pb-2">
                <Telescope className="w-8 h-8 text-gray-500" />
                <CardTitle className="text-gray-400">Hero Detail Drilldown</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  (Coming Soon) Dive into in-depth analysis for individual heroes, including matchup data and performance trends.
                </CardDescription>
              </CardContent>
          </Card>

          <Card className="bg-gray-800 border-gray-700 h-full opacity-50">
             <CardHeader className="flex flex-row items-center gap-4 pb-2">
                <Swords className="w-8 h-8 text-gray-500" />
                <CardTitle className="text-gray-400">Head-to-Head</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  (Coming Soon) Directly compare stats between two teams or two heroes to analyze their historical performance.
                </CardDescription>
              </CardContent>
          </Card>
        </section>

        {/* Data Source and Tech Stack Section */}
        <section className="grid md:grid-cols-3 gap-6 mt-12">
          <Card className="md:col-span-2 bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Technology Stack</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <span className="bg-gray-700 text-gray-300 text-sm font-medium px-3 py-1 rounded-full">Next.js</span>
                <span className="bg-gray-700 text-gray-300 text-sm font-medium px-3 py-1 rounded-full">FastAPI</span>
                <span className="bg-gray-700 text-gray-300 text-sm font-medium px-3 py-1 rounded-full">PostgreSQL</span>
                <span className="bg-gray-700 text-gray-300 text-sm font-medium px-3 py-1 rounded-full">Celery</span>
                <span className="bg-gray-700 text-gray-300 text-sm font-medium px-3 py-1 rounded-full">Redis</span>
                <span className="bg-gray-700 text-gray-300 text-sm font-medium px-3 py-1 rounded-full">Tailwind CSS</span>
                <span className="bg-gray-700 text-gray-300 text-sm font-medium px-3 py-1 rounded-full">Shadcn/UI</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-800 border-gray-700 flex flex-col items-center justify-center text-center">
            <CardHeader>
              <CardTitle className="text-white">Data Source</CardTitle>
            </CardHeader>
            <CardContent>
              <Image 
                src="/Liquipedia_logo.png" 
                alt="Liquipedia Logo" 
                width={150} 
                height={150} 
                className="mb-4"
              />
              <a 
                href="https://liquipedia.net/mobilelegends/Main_Page" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-blue-400 hover:underline text-sm"
              >
                All data is sourced from the Liquipedia API.
              </a>
            </CardContent>
          </Card>
        </section>
      </main>

      {/* Footer */}
      <footer className="container mx-auto text-center py-6 mt-8 border-t border-gray-800">
        <div className="flex items-center justify-center gap-2 mb-2">
            <Image 
                src="/beruangbatubata.png"
                alt="Creator Logo" 
                width={24} 
                height={24} 
                className="rounded-full"
            />
            <p className="text-sm text-gray-500">
              Created by BeruangBatuBata
            </p>
        </div>
        <p className="text-xs text-gray-600">
          Text content is licensed under <a href="https://creativecommons.org/licenses/by-sa/3.0/" target="_blank" rel="noopener noreferrer" className="hover:underline">CC BY-SA 3.0</a>.
        </p>
      </footer>
    </>
  );
}