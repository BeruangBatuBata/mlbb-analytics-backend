"use client";

import { useState, useEffect, useMemo } from 'react';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { Check, ChevronsUpDown, X } from "lucide-react";
import { cn } from "@/lib/utils";

// --- Type Definitions ---
interface HeroStat {
  hero_name: string;
  picks: number;
  bans: number;
  wins: number;
  losses: number;
  pick_rate: number;
  ban_rate: number;
  presence: number;
  win_rate: number;
  blue_picks: number;
  blue_wins: number;
  red_picks: number;
  red_wins: number;
}

interface SummaryStats {
  total_matches?: number;
  total_games?: number;
  total_heroes?: number;
  most_picked?: HeroStat;
  highest_win_rate?: HeroStat;
}

interface Tournament { id: number; name: string; }
interface Team { id: number; name: string; }

// --- Reusable Components ---
const StatCard = ({ title, value, subValue }: { title: string; value: string | number; subValue?: string }) => (
  <div className="bg-gray-800 p-4 rounded-lg shadow-md h-full">
    <p className="text-sm text-gray-400">{title}</p>
    <p className="text-2xl font-bold">{value}</p>
    {subValue && <p className="text-xs text-gray-500">{subValue}</p>}
  </div>
);

// --- Main Page Component ---
export default function StatisticsPage() {
  // --- State Management ---
  const [heroStats, setHeroStats] = useState<HeroStat[] | null>(null);
  const [summary, setSummary] = useState<SummaryStats>({});
  
  // State for filter options
  const [allTournaments, setAllTournaments] = useState<Tournament[]>([]);
  const [allTeams, setAllTeams] = useState<Team[]>([]);
  const [stageOptions, setStageOptions] = useState<string[]>([]);
  const [teamOptions, setTeamOptions] = useState<Team[]>([]);

  // State for selected filter values
  const [selectedTournaments, setSelectedTournaments] = useState<Tournament[]>([]);
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [selectedTeams, setSelectedTeams] = useState<Team[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');
  const [sortColumn, setSortColumn] = useState<keyof HeroStat | 'blue_win_rate' | 'red_win_rate'>('presence');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  
  const isStageFilterDisabled = selectedTournaments.length === 0;

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

  // --- Data Fetching ---
  useEffect(() => {
    // Fetch initial, unfiltered options for Tournaments and Teams
    async function fetchInitialOptions() {
        try {
            const [tournamentsRes, teamsRes] = await Promise.all([
                fetch(`${apiUrl}/api/tournaments`),
                fetch(`${apiUrl}/api/teams`),
            ]);
            if (!tournamentsRes.ok || !teamsRes.ok) throw new Error('Failed to fetch initial filter data');
            const tournamentsData = await tournamentsRes.json();
            const teamsData = await teamsRes.json();
            setAllTournaments(tournamentsData);
            setAllTeams(teamsData);
            setTeamOptions(teamsData); // Initially, team options are all teams
        } catch (e) { console.error(e); }
    }
    fetchInitialOptions();
  }, [apiUrl]);

  useEffect(() => {
    // This effect handles the cascading filter logic
    const tournamentNames = selectedTournaments.map(t => t.name);
    
    // If no tournaments are selected, disable stages and reset options
    if (tournamentNames.length === 0) {
        setStageOptions([]);
        setSelectedStages([]); // Clear selected stages
        setTeamOptions(allTeams); // Reset team options to show all teams
        // also clear selected teams that might not be in the global list anymore
        setSelectedTeams(prev => prev.filter(selectedTeam => allTeams.some(option => option.id === selectedTeam.id)));
        return;
    }

    // Fetch contextual stages and teams based on selected tournaments
    async function fetchContextualOptions() {
        const params = new URLSearchParams();
        tournamentNames.forEach(name => params.append('tournaments', name));
        
        try {
            const [stagesRes, teamsRes] = await Promise.all([
                fetch(`${apiUrl}/api/stages?${params.toString()}`),
                fetch(`${apiUrl}/api/teams?${params.toString()}`),
            ]);
            if (!stagesRes.ok || !teamsRes.ok) throw new Error('Failed to fetch contextual filter data');
            
            const newStageOptions = await stagesRes.json();
            const newTeamOptions = await teamsRes.json();
            setStageOptions(newStageOptions);
            setTeamOptions(newTeamOptions);

            // Clear any previously selected stages or teams that are no longer valid
            setSelectedStages(prev => prev.filter(s => newStageOptions.includes(s)));
            setSelectedTeams(prev => prev.filter(selectedTeam => newTeamOptions.some((option: Team) => option.id === selectedTeam.id)));

        } catch (e) { console.error(e); }
    }
    fetchContextualOptions();
  }, [selectedTournaments, allTeams, apiUrl]);

  useEffect(() => {
    // Fetch main stats whenever any filter changes
    async function fetchStats() {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      selectedTournaments.forEach(t => params.append('tournaments', t.name));
      selectedStages.forEach(s => params.append('stages', s));
      selectedTeams.forEach(t => params.append('teams', t.name));
      try {
        const response = await fetch(`${apiUrl}/api/stats?${params.toString()}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        setHeroStats(data.heroes || []);
        setSummary(data.summary || {});
      } catch (e) {
        if (e instanceof Error) setError(e.message);
        else setError("An unknown error occurred");
      } finally { setLoading(false); }
    }
    fetchStats();
  }, [selectedTournaments, selectedStages, selectedTeams, apiUrl]);

  const processedStats = useMemo(() => {
    const stats = heroStats || [];
    const filtered = filter ? stats.filter(s => s.hero_name.toLowerCase().includes(filter.toLowerCase())) : stats;
    const sortable = [...filtered];
    if (sortColumn) {
        sortable.sort((a, b) => {
            if (sortColumn === 'blue_win_rate') {
                const aVal = a.blue_picks > 0 ? (a.blue_wins / a.blue_picks) : 0;
                const bVal = b.blue_picks > 0 ? (b.blue_wins / b.blue_picks) : 0;
                return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
            }
            if (sortColumn === 'red_win_rate') {
                const aVal = a.red_picks > 0 ? (a.red_wins / a.red_picks) : 0;
                const bVal = b.red_picks > 0 ? (b.red_wins / b.red_picks) : 0;
                return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
            }
            const aVal = a[sortColumn as keyof HeroStat];
            const bVal = b[sortColumn as keyof HeroStat];
            if (typeof aVal === 'string' && typeof bVal === 'string') {
                return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }
            if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }
    return sortable;
  }, [heroStats, filter, sortColumn, sortDirection]);

  // Event Handlers
  const handleSort = (column: keyof HeroStat | 'blue_win_rate' | 'red_win_rate') => {
    if (sortColumn === column) setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    else { setSortColumn(column); setSortDirection('desc'); }
  };
  const getSortIndicator = (column: keyof HeroStat | 'blue_win_rate' | 'red_win_rate') => (sortColumn === column) ? (sortDirection === 'asc' ? ' ▲' : ' ▼') : null;
  const handleTournamentSelect = (tournament: Tournament) => { setSelectedTournaments(prev => prev.some(t => t.id === tournament.id) ? prev.filter(t => t.id !== tournament.id) : [...prev, tournament]); };
  const handleStageSelect = (stage: string) => { setSelectedStages(prev => prev.includes(stage) ? prev.filter(s => s !== stage) : [...prev, stage]); };
  const handleTeamSelect = (team: Team) => { setSelectedTeams(prev => prev.some(t => t.id === team.id) ? prev.filter(t => t.id !== team.id) : [...prev, team]); };

  return (
    <main className="container mx-auto p-4 md:p-8">
      <h1 className="text-3xl font-bold mb-2 text-center">Statistics Breakdown</h1>
      <p className="text-center text-gray-400 mb-6">Analyze the meta by filtering by tournaments, stages, and teams.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Tournament Filter */}
        <Popover><PopoverTrigger asChild>
            <button className="justify-between w-full px-4 py-2 text-left font-normal bg-gray-800 border border-gray-600 rounded-md flex items-center">
                <span className="truncate pr-2">{selectedTournaments.length > 0 ? `${selectedTournaments.length} tournament(s) selected` : "Filter by Tournament..."}</span><ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </button>
        </PopoverTrigger><PopoverContent className="w-[--radix-popover-trigger-width] p-0 bg-gray-800 border-gray-600"><Command><CommandInput placeholder="Search..." /><CommandList><CommandEmpty>No results found.</CommandEmpty><CommandGroup>
            {allTournaments.map((t) => (<CommandItem key={t.id} onSelect={() => handleTournamentSelect(t)} className="aria-selected:bg-gray-700">
                <Check className={cn("mr-2 h-4 w-4", selectedTournaments.some(st => st.id === t.id) ? "opacity-100" : "opacity-0")} />{t.name}
            </CommandItem>))}
        </CommandGroup></CommandList></Command></PopoverContent></Popover>

        {/* Stage Filter (with disabled logic) */}
        <Popover><PopoverTrigger asChild>
             <button disabled={isStageFilterDisabled} className="justify-between w-full px-4 py-2 text-left font-normal bg-gray-800 border border-gray-600 rounded-md flex items-center disabled:opacity-50 disabled:cursor-not-allowed">
                <span className="truncate pr-2">{selectedStages.length > 0 ? `${selectedStages.length} stage(s) selected` : "Filter by Stage..."}</span><ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </button>
        </PopoverTrigger><PopoverContent className="w-[--radix-popover-trigger-width] p-0 bg-gray-800 border-gray-600"><Command><CommandInput placeholder="Search..." /><CommandList><CommandEmpty>No stages found for this tournament.</CommandEmpty><CommandGroup>
            {stageOptions.map((s) => (<CommandItem key={s} onSelect={() => handleStageSelect(s)} className="aria-selected:bg-gray-700">
                <Check className={cn("mr-2 h-4 w-4", selectedStages.includes(s) ? "opacity-100" : "opacity-0")} />{s}
            </CommandItem>))}
        </CommandGroup></CommandList></Command></PopoverContent></Popover>

        {/* Team Filter */}
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

      <div className="flex flex-wrap gap-2 mb-6 min-h-[2rem]">
          {selectedTournaments.map(t => (<Badge key={`t-${t.id}`} variant="secondary" className="bg-blue-900/50 text-blue-300 border-blue-700">{t.name}<button onClick={() => handleTournamentSelect(t)} className="ml-2 rounded-full outline-none"><X className="h-3 w-3" /></button></Badge>))}
          {selectedStages.map(s => (<Badge key={`s-${s}`} variant="secondary" className="bg-purple-900/50 text-purple-300 border-purple-700">{s}<button onClick={() => handleStageSelect(s)} className="ml-2 rounded-full outline-none"><X className="h-3 w-3" /></button></Badge>))}
          {selectedTeams.map(t => (<Badge key={`team-${t.id}`} variant="secondary" className="bg-green-900/50 text-green-300 border-green-700">{t.name}<button onClick={() => handleTeamSelect(t)} className="ml-2 rounded-full outline-none"><X className="h-3 w-3" /></button></Badge>))}
      </div>
      
      {loading ? (<p className="text-center mt-8 animate-pulse">Loading statistics...</p>) 
      : error ? (<p className="text-center mt-8 text-red-500">Error: {error}</p>) 
      : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <StatCard title="Total Matches" value={summary.total_matches ?? 0} />
            <StatCard title="Total Games" value={summary.total_games ?? 0} />
            <StatCard title="Total Heroes" value={summary.total_heroes ?? 0} />
            <StatCard title="Most Picked" value={summary.most_picked?.hero_name ?? 'N/A'} subValue={`${summary.most_picked?.picks ?? 0} picks`} />
            <StatCard title="Highest Win Rate" value={summary.highest_win_rate?.hero_name ?? 'N/A'} subValue={`${summary.highest_win_rate?.win_rate?.toFixed(2) ?? '0.00'}% WR`} />
          </div>
          
          <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
            <input type="text" placeholder="Filter by hero name..." value={filter} onChange={(e) => setFilter(e.target.value)} className="w-full p-2 mb-4 border border-gray-600 rounded bg-gray-700 text-white placeholder-gray-400" />
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-700/50">
                  <tr>
                    <th className="p-3 text-left font-semibold uppercase tracking-wider">No.</th>
                    <th className="p-3 text-left font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('hero_name')}>Hero{getSortIndicator('hero_name')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('picks')}>Picks{getSortIndicator('picks')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('bans')}>Bans{getSortIndicator('bans')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('wins')}>Wins{getSortIndicator('wins')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('pick_rate')}>Pick %{getSortIndicator('pick_rate')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('ban_rate')}>Ban %{getSortIndicator('ban_rate')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('presence')}>Presence %{getSortIndicator('presence')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('win_rate')}>Win %{getSortIndicator('win_rate')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('blue_picks')}>Blue Picks{getSortIndicator('blue_picks')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('blue_wins')}>Blue Wins{getSortIndicator('blue_wins')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('blue_win_rate')}>Blue WR %{getSortIndicator('blue_win_rate')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('red_picks')}>Red Picks{getSortIndicator('red_picks')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('red_wins')}>Red Wins{getSortIndicator('red_wins')}</th>
                    <th className="p-3 text-center font-semibold uppercase tracking-wider cursor-pointer" onClick={() => handleSort('red_win_rate')}>Red WR %{getSortIndicator('red_win_rate')}</th>
                  </tr>
                </thead>
                <tbody>
                  {processedStats.map((stat, index) => {
                    const blueWinRate = stat.blue_picks > 0 ? (stat.blue_wins / stat.blue_picks) * 100 : 0;
                    const redWinRate = stat.red_picks > 0 ? (stat.red_wins / stat.red_picks) * 100 : 0;
                    return (
                      <tr key={stat.hero_name} className="border-b border-gray-700 hover:bg-gray-700/50">
                        <td className="p-3 text-center font-medium text-gray-400">{index + 1}</td>
                        <td className="p-3 font-medium whitespace-nowrap">{stat.hero_name}</td>
                        <td className="p-3 text-center">{stat.picks}</td>
                        <td className="p-3 text-center">{stat.bans}</td>
                        <td className="p-3 text-center">{stat.wins}</td>
                        <td className="p-3 text-center">{stat.pick_rate.toFixed(2)}%</td>
                        <td className="p-3 text-center">{stat.ban_rate.toFixed(2)}%</td>
                        <td className="p-3 text-center">{stat.presence.toFixed(2)}%</td>
                        <td className="p-3 text-center">{stat.win_rate.toFixed(2)}%</td>
                        <td className="p-3 text-center">{stat.blue_picks}</td>
                        <td className="p-3 text-center">{stat.blue_wins}</td>
                        <td className="p-3 text-center">{blueWinRate.toFixed(2)}%</td>
                        <td className="p-3 text-center">{stat.red_picks}</td>
                        <td className="p-3 text-center">{stat.red_wins}</td>
                        <td className="p-3 text-center">{redWinRate.toFixed(2)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </main>
  );
}

