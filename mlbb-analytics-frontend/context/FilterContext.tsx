// In mlbb-analytics-frontend/context/FilterContext.tsx

'use client';

import { createContext, useContext, useState, ReactNode, Dispatch, SetStateAction } from 'react';

// Type definitions for our filters
interface Tournament { id: number; name: string; }
interface Team { id: number; name: string; }

// Define the shape of our context state
interface FilterContextType {
  selectedTournaments: Tournament[];
  setSelectedTournaments: Dispatch<SetStateAction<Tournament[]>>;
  selectedStages: string[];
  setSelectedStages: Dispatch<SetStateAction<string[]>>;
  selectedTeams: Team[];
  setSelectedTeams: Dispatch<SetStateAction<Team[]>>;
}

// Create the context with a default value
const FilterContext = createContext<FilterContextType | undefined>(undefined);

// Create the Provider component that will wrap our application
export function FilterProvider({ children }: { children: ReactNode }) {
  const [selectedTournaments, setSelectedTournaments] = useState<Tournament[]>([]);
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [selectedTeams, setSelectedTeams] = useState<Team[]>([]);

  const value = {
    selectedTournaments,
    setSelectedTournaments,
    selectedStages,
    setSelectedStages,
    selectedTeams,
    setSelectedTeams,
  };

  return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>;
}

// Create a custom hook for easy access to the context
export function useFilters() {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error('useFilters must be used within a FilterProvider');
  }
  return context;
}