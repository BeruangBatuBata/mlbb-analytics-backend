'use client';

import { createContext, useContext, useState, ReactNode, Dispatch, SetStateAction } from 'react';

// Type definitions
interface Tournament { id: number; name: string; }
interface Team { id: number; name: string; }
export type GroupingMode = 'split' | 'region';

// Context state shape
interface FilterContextType {
  selectedTournaments: Tournament[];
  setSelectedTournaments: Dispatch<SetStateAction<Tournament[]>>;
  selectedStages: string[];
  setSelectedStages: Dispatch<SetStateAction<string[]>>;
  selectedTeams: Team[];
  setSelectedTeams: Dispatch<SetStateAction<Team[]>>;
  groupingMode: GroupingMode;
  setGroupingMode: Dispatch<SetStateAction<GroupingMode>>;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [selectedTournaments, setSelectedTournaments] = useState<Tournament[]>([]);
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [selectedTeams, setSelectedTeams] = useState<Team[]>([]);
  const [groupingMode, setGroupingMode] = useState<GroupingMode>('split');

  const value = {
    selectedTournaments,
    setSelectedTournaments,
    selectedStages,
    setSelectedStages,
    selectedTeams,
    setSelectedTeams,
    groupingMode,
    setGroupingMode,
  };

  return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>;
}

export function useFilters() {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error('useFilters must be used within a FilterProvider');
  }
  return context;
}