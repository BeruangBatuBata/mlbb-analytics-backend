'use client';

import { useState, useEffect } from 'react';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

// --- Type Definitions ---
interface Tournament { id: number; name: string; }
type GroupedTournaments = Record<string, Tournament[]>;

interface TwoPanelSelectorProps {
  groupedTournaments: GroupedTournaments;
  selectedTournaments: Tournament[];
  onSelectionChange: (tournaments: Tournament[]) => void;
}

export function TwoPanelSelector({ groupedTournaments, selectedTournaments, onSelectionChange }: TwoPanelSelectorProps) {
  const groupKeys = Object.keys(groupedTournaments).sort((a, b) => b.localeCompare(a));
  const [activeGroup, setActiveGroup] = useState<string | null>(null);

  // Effect to set the initial or reset active group
  useEffect(() => {
    if ((!activeGroup && groupKeys.length > 0) || (activeGroup && !groupKeys.includes(activeGroup))) {
      setActiveGroup(groupKeys.length > 0 ? groupKeys[0] : null);
    }
  }, [groupKeys, activeGroup]);

  const tournamentsInActiveGroup = activeGroup ? groupedTournaments[activeGroup] || [] : [];
  const selectedIds = new Set(selectedTournaments.map(t => t.id));

  const handleGroupSelectAll = () => {
    if (!activeGroup) return;
    const groupIds = new Set(tournamentsInActiveGroup.map(t => t.id));
    const otherSelected = selectedTournaments.filter(t => !groupIds.has(t.id));
    onSelectionChange([...otherSelected, ...tournamentsInActiveGroup]);
  };

  const handleGroupDeselectAll = () => {
    if (!activeGroup) return;
    const groupIds = new Set(tournamentsInActiveGroup.map(t => t.id));
    onSelectionChange(selectedTournaments.filter(t => !groupIds.has(t.id)));
  };

  const handleItemToggle = (tournament: Tournament) => {
    onSelectionChange(
      selectedIds.has(tournament.id)
        ? selectedTournaments.filter(t => t.id !== tournament.id)
        : [...selectedTournaments, tournament]
    );
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="justify-between w-full px-4 py-2 text-left font-normal bg-gray-800 border border-gray-600 rounded-md flex items-center">
          <span className="truncate pr-2">{selectedTournaments.length > 0 ? `${selectedTournaments.length} tournament(s) selected` : "Filter by Tournament..."}</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-[450px] p-0 bg-gray-900 border-gray-700" align="start">
        <div className="flex h-[300px]">
          {/* Left Panel: Groups */}
          <div className="w-1/3 border-r border-gray-700 overflow-y-auto">
            {groupKeys.map(key => (
              <button
                key={key}
                onClick={() => setActiveGroup(key)}
                className={cn(
                  "w-full text-left p-2 text-sm hover:bg-gray-800",
                  activeGroup === key && "bg-blue-900/50"
                )}
              >
                {key}
              </button>
            ))}
          </div>
          {/* Right Panel: Items */}
          <div className="w-2/3 flex flex-col">
            {activeGroup && (
              <>
                <div className="p-2 border-b border-gray-700 flex justify-between items-center">
                   <h4 className="font-semibold text-sm truncate pr-2">{activeGroup}</h4>
                   <div className='flex-shrink-0'>
                       <Button variant="link" size="sm" className="p-0 h-auto text-xs" onClick={handleGroupSelectAll}>All</Button>
                       <span className="mx-1 text-gray-500">/</span>
                       <Button variant="link" size="sm" className="p-0 h-auto text-xs" onClick={handleGroupDeselectAll}>None</Button>
                   </div>
                </div>
                <div className="flex-grow overflow-y-auto">
                  {tournamentsInActiveGroup.map(t => (
                    <div key={t.id} className="flex items-center p-2 hover:bg-gray-800">
                      <Checkbox
                        id={`t-${t.id}`}
                        checked={selectedIds.has(t.id)}
                        onCheckedChange={() => handleItemToggle(t)}
                        className="mr-2"
                      />
                      <label htmlFor={`t-${t.id}`} className="text-sm cursor-pointer">{t.name}</label>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}