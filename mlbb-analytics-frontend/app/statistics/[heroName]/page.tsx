// In mlbb-analytics-frontend/app/statistics/[heroName]/page.tsx

'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation'; // <-- Import useRouter
import { useFilters } from '@/context/FilterContext';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Check, ChevronsUpDown, X } from "lucide-react";
import { cn } from "@/lib/utils";

// --- Type Definitions ---
interface HeroPerformanceByTeam { team_name: string; games_played: number; wins: number; win_rate: number; }
interface HeroPerformanceVsOpponent { opponent_hero_name: string; games_faced: number; wins_against: number; win_rate_vs: number; }
interface HeroDetails { by_team: HeroPerformanceByTeam[]; vs_opponents: HeroPerformanceVsOpponent[]; }
interface Tournament { id: number; name: string; }
interface Team { id: number; name: string; }

export default function HeroDetailPage({ params }: { params: Promise<{ heroName: string }> }) {
  const awaitedParams = use(params);
  const router = useRouter(); // <-- Initialize router
  const heroName = decodeURIComponent(awaitedParams.heroName);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

  // --- State ---
  const [heroDetails, setHeroDetails] = useState<HeroDetails | null>(null);
  const [allHeroes, setAllHeroes] = useState<string[]>([]); // <-- New state for hero list
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter options and selections from context
  const [allTournaments, setAllTournaments] = useState<Tournament[]>([]);
  const [allTeams, setAllTeams] = useState<Team[]>([]);
  const [stageOptions, setStageOptions] = useState<string[]>([]);
  const [teamOptions, setTeamOptions] = useState<Team[]>([]);
  const { selectedTournaments, setSelectedTournaments, selectedStages, setSelectedStages, selectedTeams, setSelectedTeams } = useFilters();
  const isStageFilterDisabled = selectedTournaments.length === 0;

  // --- Data Fetching ---
  useEffect(() => {
    // Fetch the list of all heroes for the dropdown
    async function fetchAllHeroes() {
      try {
        const response = await fetch(`${apiUrl}/api/heroes`);
        if (!response.ok) throw new Error('Failed to fetch hero list');
        const data = await response.json();
        setAllHeroes(data);
      } catch (e) { console.error(e) }
    }
    fetchAllHeroes();
  }, [apiUrl]);

  useEffect(() => {
    async function fetchInitialOptions() {
      try {
        const [tournamentsRes, teamsRes] = await Promise.all([fetch(`${apiUrl}/api/tournaments`), fetch(`${apiUrl}/api/teams`)]);
        if (!tournamentsRes.ok || !teamsRes.ok) throw new Error('Failed to fetch initial filter data');
        const tournamentsData = await tournamentsRes.json();
        const teamsData = await teamsRes.json();
        setAllTournaments(tournamentsData);
        setAllTeams(teamsData);
        setTeamOptions(teamsData);
      } catch (e) { console.error(e); }
    }
    fetchInitialOptions();
  }, [apiUrl]);

  useEffect(() => {
    const tournamentNames = selectedTournaments.map(t => t.name);
    if (tournamentNames.length === 0) {
      setStageOptions([]);
      setSelectedStages([]);
      setTeamOptions(allTeams);
      setSelectedTeams(prev => prev.filter(st => allTeams.some(opt => opt.id === st.id)));
      return;
    }
    async function fetchContextualOptions() {
      const params = new URLSearchParams();
      tournamentNames.forEach(name => params.append('tournaments', name));
      try {
        const [stagesRes, teamsRes] = await Promise.all([fetch(`${apiUrl}/api/stages?${params.toString()}`), fetch(`${apiUrl}/api/teams?${params.toString()}`)]);
        if (!stagesRes.ok || !teamsRes.ok) throw new Error('Failed to fetch contextual data');
        const newStageOptions: string[] = await stagesRes.json();
        const newTeamOptions: Team[] = await teamsRes.json();
        setStageOptions(newStageOptions);
        setTeamOptions(newTeamOptions);
        setSelectedStages(prev => prev.filter(s => newStageOptions.includes(s)));
        setSelectedTeams(prev => prev.filter(st => newTeamOptions.some(opt => opt.id === st.id)));
      } catch (e) { console.error(e); }
    }
    fetchContextualOptions();
  }, [selectedTournaments, allTeams, apiUrl, setSelectedStages, setSelectedTeams]);

  useEffect(() => {
    async function fetchHeroDetails() {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      selectedTournaments.forEach(t => params.append('tournaments', t.name));
      selectedStages.forEach(s => params.append('stages', s));
      selectedTeams.forEach(t => params.append('teams', t.name));
      try {
        const response = await fetch(`${apiUrl}/api/heroes/${encodeURIComponent(heroName)}?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch hero details');
        const data: HeroDetails = await response.json();
        setHeroDetails(data);
      } catch (err) { setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally { setLoading(false); }
    };
    if (heroName) fetchHeroDetails();
  }, [heroName, selectedTournaments, selectedStages, selectedTeams, apiUrl]);

  // --- Handlers ---
  const handleHeroChange = (newHeroName: string) => {
    if (newHeroName && newHeroName !== heroName) {
      router.push(`/statistics/${encodeURIComponent(newHeroName)}`);
    }
  };
  const handleTournamentSelect = (tournament: Tournament) => setSelectedTournaments(prev => prev.some(t => t.id === tournament.id) ? prev.filter(t => t.id !== tournament.id) : [...prev, tournament]);
  const handleStageSelect = (stage: string) => setSelectedStages(prev => prev.includes(stage) ? prev.filter(s => s !== stage) : [...prev, stage]);
  const handleTeamSelect = (team: Team) => setSelectedTeams(prev => prev.some(t => t.id === team.id) ? prev.filter(t => t.id !== team.id) : [...prev, team]);

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold whitespace-nowrap">Stats for</h1>
          {/* --- HERO SELECTOR DROPDOWN --- */}
          <Popover>
            <PopoverTrigger asChild>
              <button className="justify-between min-w-[200px] px-4 py-2 text-xl font-bold bg-gray-800 border border-gray-600 rounded-md flex items-center">
                <span className="truncate pr-2">{heroName}</span>
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-[--radix-popover-trigger-width] p-0 bg-gray-800 border-gray-600">
              <Command>
                <CommandInput placeholder="Search hero..." />
                <CommandList>
                  <CommandEmpty>No hero found.</CommandEmpty>
                  <CommandGroup>
                    {allHeroes.map((name) => (
                      <CommandItem key={name} onSelect={() => handleHeroChange(name)}>
                        <Check className={cn("mr-2 h-4 w-4", heroName === name ? "opacity-100" : "opacity-0")} />
                        {name}
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>
        <Link href="/statistics" className="text-blue-500 hover:underline self-end sm:self-center">&larr; Back to Statistics</Link>
      </div>
      
      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* ... (filter component JSX remains exactly the same) ... */}
         <Popover><PopoverTrigger asChild>
          <button className="justify-between w-full px-4 py-2 text-left font-normal bg-gray-800 border border-gray-600 rounded-md flex items-center">
            <span className="truncate pr-2">{selectedTournaments.length > 0 ? `${selectedTournaments.length} tournament(s) selected` : "Filter by Tournament..."}</span><ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </button>
        </PopoverTrigger><PopoverContent className="w-[--radix-popover-trigger-width] p-0 bg-gray-800 border-gray-600"><Command><CommandInput placeholder="Search..." /><CommandList><CommandEmpty>No results found.</CommandEmpty><CommandGroup>
            {allTournaments.map((t) => (<CommandItem key={t.id} onSelect={() => handleTournamentSelect(t)} className="aria-selected:bg-gray-700">
                <Check className={cn("mr-2 h-4 w-4", selectedTournaments.some(st => st.id === t.id) ? "opacity-100" : "opacity-0")} />{t.name}
            </CommandItem>))}
        </CommandGroup></CommandList></Command></PopoverContent></Popover>
        <Popover><PopoverTrigger asChild>
             <button disabled={isStageFilterDisabled} className="justify-between w-full px-4 py-2 text-left font-normal bg-gray-800 border border-gray-600 rounded-md flex items-center disabled:opacity-50 disabled:cursor-not-allowed">
                <span className="truncate pr-2">{selectedStages.length > 0 ? `${selectedStages.length} stage(s) selected` : "Filter by Stage..."}</span><ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </button>
        </PopoverTrigger><PopoverContent className="w-[--radix-popover-trigger-width] p-0 bg-gray-800 border-gray-600"><Command><CommandInput placeholder="Search..." /><CommandList><CommandEmpty>No stages found.</CommandEmpty><CommandGroup>
            {stageOptions.map((s) => (<CommandItem key={s} onSelect={() => handleStageSelect(s)} className="aria-selected:bg-gray-700">
                <Check className={cn("mr-2 h-4 w-4", selectedStages.includes(s) ? "opacity-100" : "opacity-0")} />{s}
            </CommandItem>))}
        </CommandGroup></CommandList></Command></PopoverContent></Popover>
        <Popover><PopoverTrigger asChild>
             <button className="justify-between w-full px-4 py-2 text-left font-normal bg-gray-800 border border-gray-600 rounded-md flex items-center">
                <span className="truncate pr-2">{selectedTeams.length > 0 ? `${selectedTeams.length} team(s) selected` : "Filter by Team..."}</span><ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </button>
        </PopoverTrigger><PopoverContent className="w-[--radix-popover-trigger-width] p-0 bg-gray-800 border-gray-600"><Command><CommandInput placeholder="Search..." /><CommandList><CommandEmpty>No teams found.</CommandEmpty><CommandGroup>
            {teamOptions.map((t) => (<CommandItem key={t.id} onSelect={() => handleTeamSelect(t)} className="aria-selected:bg-gray-700">
                <Check className={cn("mr-2 h-4 w-4", selectedTeams.some(st => st.id === t.id) ? "opacity-100" : "opacity-0")} />{t.name}
            </CommandItem>))}
        </CommandGroup></CommandList></Command></PopoverContent></Popover>
      </div>
      <div className="flex flex-wrap gap-2 min-h-[2rem]">
          {selectedTournaments.map((t) => (<Badge key={`t-${t.id}`} variant="secondary" className="bg-blue-900/50 text-blue-300 border-blue-700">{t.name}<button onClick={() => handleTournamentSelect(t)} className="ml-2 rounded-full outline-none"><X className="h-3 w-3" /></button></Badge>))}
          {selectedStages.map((s) => (<Badge key={`s-${s}`} variant="secondary" className="bg-purple-900/50 text-purple-300 border-purple-700">{s}<button onClick={() => handleStageSelect(s)} className="ml-2 rounded-full outline-none"><X className="h-3 w-3" /></button></Badge>))}
          {selectedTeams.map((t) => (<Badge key={`team-${t.id}`} variant="secondary" className="bg-green-900/50 text-green-300 border-green-700">{t.name}<button onClick={() => handleTeamSelect(t)} className="ml-2 rounded-full outline-none"><X className="h-3 w-3" /></button></Badge>))}
      </div>

      {/* Data Display */}
      {loading ? (<div className="text-center mt-8 animate-pulse">Loading hero details...</div>)
      : error ? (<div className="text-center mt-8 text-red-500">Error: {error}</div>)
      : !heroDetails ? (<div className="text-center mt-8">No data found for {heroName}.</div>)
      : (
        <>
          {/* ... (Card and Table JSX for data display remains the same) ... */}
           <Card>
            <CardHeader><CardTitle>Performance by Team</CardTitle></CardHeader>
            <CardContent><Table>
              <TableHeader><TableRow>
                <TableHead>Team</TableHead>
                <TableHead className="text-right">Games Played</TableHead>
                <TableHead className="text-right">Wins</TableHead>
                <TableHead className="text-right">Win Rate</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {heroDetails.by_team.map((row) => (
                  <TableRow key={row.team_name}>
                    <TableCell>{row.team_name}</TableCell>
                    <TableCell className="text-right">{row.games_played}</TableCell>
                    <TableCell className="text-right">{row.wins}</TableCell>
                    <TableCell className="text-right">{row.win_rate.toFixed(2)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table></CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Matchups vs. Opposing Heroes</CardTitle></CardHeader>
            <CardContent><Table>
              <TableHeader><TableRow>
                <TableHead>Opponent Hero</TableHead>
                <TableHead className="text-right">Games Faced</TableHead>
                <TableHead className="text-right">Wins Against</TableHead>
                <TableHead className="text-right">Win Rate vs.</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {heroDetails.vs_opponents.map((row) => (
                  <TableRow key={row.opponent_hero_name}>
                    <TableCell>{row.opponent_hero_name}</TableCell>
                    <TableCell className="text-right">{row.games_faced}</TableCell>
                    <TableCell className="text-right">{row.wins_against}</TableCell>
                    <TableCell className="text-right">{row.win_rate_vs.toFixed(2)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table></CardContent>
          </Card>
        </>
      )}
    </div>
  );
}