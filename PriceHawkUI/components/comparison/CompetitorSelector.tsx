'use client';

import { CompetitorRetailer, CompetitorInfo } from '@/lib/types/manual-comparison';
import { COMPETITOR_LIST } from '@/lib/constants/competitors';
import { Check, Square, CheckSquare } from 'lucide-react';

interface CompetitorSelectorProps {
  selectedCompetitors: CompetitorRetailer[];
  onSelectionChange: (competitors: CompetitorRetailer[]) => void;
  disabled?: boolean;
}

export function CompetitorSelector({
  selectedCompetitors,
  onSelectionChange,
  disabled = false,
}: CompetitorSelectorProps) {
  const allSelected = selectedCompetitors.length === COMPETITOR_LIST.length;
  const noneSelected = selectedCompetitors.length === 0;

  const handleToggle = (competitorId: CompetitorRetailer) => {
    if (disabled) return;

    if (selectedCompetitors.includes(competitorId)) {
      onSelectionChange(selectedCompetitors.filter(c => c !== competitorId));
    } else {
      onSelectionChange([...selectedCompetitors, competitorId]);
    }
  };

  const handleSelectAll = () => {
    if (disabled) return;

    if (allSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(COMPETITOR_LIST.map(c => c.id));
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">
          Select Competitors
        </label>
        <button
          type="button"
          onClick={handleSelectAll}
          disabled={disabled}
          className="text-sm text-sky-600 hover:text-sky-700 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          {allSelected ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {COMPETITOR_LIST.map((competitor) => (
          <CompetitorCheckbox
            key={competitor.id}
            competitor={competitor}
            checked={selectedCompetitors.includes(competitor.id)}
            onToggle={() => handleToggle(competitor.id)}
            disabled={disabled}
          />
        ))}
      </div>

      {noneSelected && (
        <p className="text-sm text-amber-600">
          Please select at least one competitor to compare
        </p>
      )}
    </div>
  );
}

interface CompetitorCheckboxProps {
  competitor: CompetitorInfo;
  checked: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

function CompetitorCheckbox({
  competitor,
  checked,
  onToggle,
  disabled = false,
}: CompetitorCheckboxProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      className={`
        flex items-center gap-2 p-3 rounded-lg border-2 transition-all
        ${checked
          ? 'border-sky-500 bg-sky-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <div className={`
        w-5 h-5 rounded flex items-center justify-center
        ${checked ? 'bg-sky-500 text-white' : 'border-2 border-gray-300'}
      `}>
        {checked && <Check className="w-3 h-3" />}
      </div>
      <div className="text-left">
        <p className="text-sm font-medium text-gray-900">{competitor.name}</p>
        <p className="text-xs text-gray-500">{competitor.nameTh}</p>
      </div>
    </button>
  );
}
