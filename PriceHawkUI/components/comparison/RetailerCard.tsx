'use client';

import { CompetitorInfo } from '@/lib/types/manual-comparison';
import { Check, Store } from 'lucide-react';
import Image from 'next/image';

interface RetailerCardProps {
  competitor: CompetitorInfo;
  isSelected: boolean;
  onSelect: () => void;
  disabled?: boolean;
}

export function RetailerCard({
  competitor,
  isSelected,
  onSelect,
  disabled = false,
}: RetailerCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      className={`
        relative w-full flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all duration-200
        min-h-[120px] hover:shadow-lg
        ${
          isSelected
            ? 'border-cyan-500 bg-cyan-50 shadow-md'
            : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
        }
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
        focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2
      `}
      aria-label={`${isSelected ? 'Deselect' : 'Select'} ${competitor.name}`}
      aria-pressed={isSelected}
    >
      {/* Checkmark Badge */}
      {isSelected && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-cyan-500 rounded-full flex items-center justify-center shadow-sm">
          <Check className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Logo */}
      <div className="w-16 h-16 flex items-center justify-center rounded-lg overflow-hidden bg-white shadow-sm">
        {competitor.logo ? (
          <Image
            src={competitor.logo}
            alt={`${competitor.name} logo`}
            width={64}
            height={64}
            className="object-contain"
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{ backgroundColor: competitor.color }}
          >
            <Store className="w-8 h-8 text-white" />
          </div>
        )}
      </div>

      {/* Retailer Name */}
      <div className="text-center">
        <h3 className="text-sm font-semibold text-gray-900">{competitor.name}</h3>
        <p className="text-xs text-gray-500 mt-0.5">{competitor.nameTh}</p>
      </div>

      {/* Brand Color Accent */}
      <div
        className="absolute bottom-0 left-0 right-0 h-1 rounded-b-xl"
        style={{ backgroundColor: competitor.color }}
      />
    </button>
  );
}
