'use client';

import { COMPETITORS, COMPETITOR_LIST } from '@/lib/constants/competitors';
import { CompetitorRetailer } from '@/lib/types/manual-comparison';
import { X, Check, Info } from 'lucide-react';
import { Tooltip } from '@/components/ui/Tooltip';
import Image from 'next/image';
import { useState } from 'react';

interface CompetitorInputCardProps {
  id: string;
  retailer: CompetitorRetailer | '';
  url: string;
  onRetailerChange: (retailer: CompetitorRetailer) => void;
  onUrlChange: (url: string) => void;
  onRemove: () => void;
  disabled?: boolean;
  error?: string;
  usedRetailers?: CompetitorRetailer[];
}

export function CompetitorInputCard({
  id,
  retailer,
  url,
  onRetailerChange,
  onUrlChange,
  onRemove,
  disabled = false,
  error,
  usedRetailers = [],
}: CompetitorInputCardProps) {
  const [showRetailerSelector, setShowRetailerSelector] = useState(!retailer);
  const selectedCompetitor = retailer ? COMPETITORS[retailer] : null;
  const isUrlValid = url.trim().length > 0 && url.startsWith('http');

  return (
    <div className="overflow-hidden rounded-xl bg-white border border-gray-200 shadow-md transition-all hover:shadow-lg duration-200">
      {/* Header */}
      <div className="flex items-center justify-between border-b-2 border-gray-200 bg-gray-50 px-4 py-3">
        <div className="flex items-center gap-2">
          {selectedCompetitor?.logo && (
            <Image
              src={selectedCompetitor.logo}
              alt={selectedCompetitor.name}
              width={24}
              height={24}
              className="object-contain"
            />
          )}
          <span className="text-sm font-bold text-gray-900">
            {selectedCompetitor?.name || 'Competitor'}
          </span>
        </div>
        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          className="rounded p-1 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500 disabled:cursor-not-allowed"
          aria-label="Remove competitor"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Form Fields */}
      <div className="space-y-4 p-4">
        {/* Retailer Visual Selection */}
        <div>
          <div className="mb-3 flex items-center gap-2">
            <label className="block text-sm font-semibold text-gray-900">
              Select Retailer {!retailer && <span className="text-red-600">*</span>}
            </label>
            <Tooltip content="Choose which retailer you want to compare against" placement="right">
              <Info className="w-4 h-4 text-gray-400 hover:text-gray-600 transition-colors" />
            </Tooltip>
          </div>

          {/* Selected Retailer - Show when retailer is selected and not showing selector */}
          {retailer && !showRetailerSelector && (
            <button
              type="button"
              onClick={() => setShowRetailerSelector(true)}
              disabled={disabled}
              className="w-full group"
            >
              <div
                className="rounded-lg border-2 p-4 transition-all duration-200 hover:shadow-md"
                style={{
                  borderColor: selectedCompetitor?.color,
                  backgroundColor: `${selectedCompetitor?.color}10`
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {selectedCompetitor?.logo && (
                      <Image
                        src={selectedCompetitor.logo}
                        alt={selectedCompetitor.name}
                        width={32}
                        height={32}
                        className="object-contain"
                      />
                    )}
                    <div className="text-left">
                      <div className="font-bold text-gray-900">{selectedCompetitor?.name}</div>
                      <div className="text-xs text-gray-600">{selectedCompetitor?.nameTh}</div>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 group-hover:text-gray-700">Change</span>
                </div>
              </div>
            </button>
          )}

          {/* Retailer Cards Grid - Show when no retailer selected or when changing */}
          {(!retailer || showRetailerSelector) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {COMPETITOR_LIST.map((comp) => {
                const isUsed = usedRetailers.includes(comp.id);
                const isCurrentSelection = retailer === comp.id;
                const isDisabled = (isUsed && !isCurrentSelection) || disabled;

                return (
                  <button
                    key={comp.id}
                    type="button"
                    onClick={() => {
                      if (!isDisabled) {
                        onRetailerChange(comp.id);
                        setShowRetailerSelector(false);
                      }
                    }}
                    disabled={isDisabled}
                    className={`
                      relative rounded-lg border-2 p-4 text-left transition-all duration-200
                      ${
                        isCurrentSelection
                          ? 'shadow-lg scale-105'
                          : isDisabled
                          ? 'opacity-50 cursor-not-allowed'
                          : 'hover:shadow-md hover:scale-105 cursor-pointer'
                      }
                    `}
                    style={{
                      borderColor: isCurrentSelection ? comp.color : '#E5E7EB',
                      backgroundColor: isCurrentSelection ? `${comp.color}10` : 'white',
                      boxShadow: isCurrentSelection ? `0 0 0 4px ${comp.color}30` : undefined,
                    }}
                  >
                    <div className="flex items-center gap-3">
                      {comp.logo && (
                        <Image
                          src={comp.logo}
                          alt={comp.name}
                          width={28}
                          height={28}
                          className="object-contain flex-shrink-0"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-gray-900 text-sm">{comp.name}</div>
                        <div className="text-xs text-gray-600 truncate">{comp.nameTh}</div>
                      </div>
                      {isCurrentSelection && (
                        <Check className="w-5 h-5 flex-shrink-0 animate-in zoom-in-50 duration-200" style={{ color: comp.color }} />
                      )}
                    </div>
                    {isUsed && !isCurrentSelection && (
                      <div className="absolute top-2 right-2">
                        <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                          Used
                        </span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {!retailer && (
            <p className="mt-2 text-xs text-gray-500 flex items-center gap-1">
              <Info className="w-3 h-3" />
              Choose a retailer to compare products from
            </p>
          )}
        </div>

        {/* Product URL Input */}
        <div>
          <div className="mb-2 flex items-center gap-2">
            <label
              htmlFor={`${id}-url`}
              className="block text-sm font-semibold text-gray-900"
            >
              Product URL {retailer && <span className="text-red-600">*</span>}
            </label>
            <Tooltip
              content={
                selectedCompetitor
                  ? `Paste the product URL from ${selectedCompetitor.name} website`
                  : 'Select a retailer first'
              }
              placement="right"
            >
              <Info className="w-4 h-4 text-gray-400 hover:text-gray-600 transition-colors" />
            </Tooltip>
          </div>
          <div
            className={`
              min-h-[52px] cursor-text rounded-lg border-2 bg-gray-50 px-4 py-3 transition-all duration-200
              ${
                error
                  ? 'border-red-400 ring-2 ring-red-100'
                  : isUrlValid && retailer
                  ? 'border-green-400 ring-2 ring-green-100'
                  : 'border-gray-200 hover:border-gray-300 focus-within:border-cyan-500 focus-within:ring-2 focus-within:ring-cyan-100 focus-within:shadow-lg'
              }
              ${!retailer ? 'opacity-50' : ''}
            `}
            onClick={() => {
              if (retailer) {
                document.getElementById(`${id}-url`)?.focus();
              }
            }}
          >
            <div className="flex items-center gap-2">
              <input
                id={`${id}-url`}
                type="url"
                value={url}
                onChange={(e) => onUrlChange(e.target.value)}
                placeholder={
                  selectedCompetitor
                    ? `https://www.${selectedCompetitor.domain}/...`
                    : 'Select a retailer first'
                }
                disabled={disabled || !retailer}
                className="flex-1 border-none bg-transparent font-medium text-gray-900 outline-none placeholder-gray-400 disabled:cursor-not-allowed disabled:opacity-50"
              />
              {isUrlValid && retailer && !error && (
                <Check className="w-5 h-5 text-green-600 flex-shrink-0 animate-in zoom-in-50 duration-200" />
              )}
            </div>
          </div>

          {error && (
            <p className="mt-1 text-xs font-medium text-red-600 flex items-center gap-1">
              <span>⚠</span> {error}
            </p>
          )}
          {!error && retailer && (
            <p className="mt-1 text-xs text-gray-500 flex items-center gap-1">
              <Info className="w-3 h-3" />
              Copy and paste the full URL from {selectedCompetitor?.name} website
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
