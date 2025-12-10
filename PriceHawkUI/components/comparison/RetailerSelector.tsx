'use client';

import { CompetitorRetailer } from '@/lib/types/manual-comparison';
import { COMPETITOR_LIST } from '@/lib/constants/competitors';
import { RetailerCard } from './RetailerCard';
import { Tooltip } from '@/components/ui/Tooltip';

interface RetailerSelectorProps {
  selectedRetailers: CompetitorRetailer[];
  onSelect: (retailer: CompetitorRetailer) => void;
  disabled?: boolean;
}

export function RetailerSelector({
  selectedRetailers,
  onSelect,
  disabled = false,
}: RetailerSelectorProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Select Retailers</h3>
        <div className="flex items-center gap-2">
          {selectedRetailers.length > 0 && (
            <span className="text-xs bg-cyan-100 text-cyan-700 px-2 py-1 rounded-full font-medium">
              {selectedRetailers.length} selected
            </span>
          )}
          <Tooltip content="Select at least one retailer to compare against" placement="left">
            <span className="text-gray-400 hover:text-gray-600 cursor-help" />
          </Tooltip>
        </div>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {COMPETITOR_LIST.map((competitor) => {
            const isSelected = selectedRetailers.includes(competitor.id);
            return (
              <RetailerCard
                key={competitor.id}
                competitor={competitor}
                isSelected={isSelected}
                onSelect={() => onSelect(competitor.id)}
                disabled={disabled}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
