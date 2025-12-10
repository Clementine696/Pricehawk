'use client';

import { ThaiWatsuduInput } from '@/lib/types/manual-comparison';
import { THAI_WATSADU_COLOR } from '@/lib/constants/competitors';
import { Tooltip } from '@/components/ui/Tooltip';
import { Check, Info } from 'lucide-react';
import Image from 'next/image';

interface ThaiWatsuduInputCardProps {
  value: ThaiWatsuduInput;
  onChange: (value: ThaiWatsuduInput) => void;
  disabled?: boolean;
  errors?: {
    sku?: string;
    url?: string;
  };
}

export function ThaiWatsuduInputCard({
  value,
  onChange,
  disabled = false,
  errors,
}: ThaiWatsuduInputCardProps) {
  const isSkuValid = value.sku.trim().length > 0;
  const isUrlValid = value.url.trim().length > 0 && value.url.startsWith('http');

  return (
    <div className="bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-600 rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-200">
      {/* Header with Thai Watsadu branding */}
      <div
        className="px-4 py-3 flex items-center gap-2"
        style={{ backgroundColor: THAI_WATSADU_COLOR }}
      >
        <Image
          src="/logos/thaiwatsadu.svg"
          alt="Thai Watsadu"
          width={24}
          height={24}
          className="object-contain"
        />
        <span className="text-sm font-bold text-white">Thai Watsadu (Source Product)</span>
      </div>

      {/* Input Fields */}
      <div className="p-6 bg-white space-y-4">
        {/* SKU Input */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <label className="block text-sm font-semibold text-gray-900">
              SKU <span className="text-red-600">*</span>
            </label>
            <Tooltip content="Enter the product SKU from Thai Watsadu catalog" placement="right">
              <Info className="w-4 h-4 text-gray-400 hover:text-gray-600 transition-colors" />
            </Tooltip>
          </div>
          <div
            className={`
              bg-gray-50 rounded-lg px-4 py-3 min-h-[52px] cursor-text border-2 transition-all duration-200
              ${
                errors?.sku
                  ? 'border-red-400 ring-2 ring-red-100'
                  : isSkuValid
                  ? 'border-green-400 ring-2 ring-green-100'
                  : 'border-gray-200 hover:border-red-300 focus-within:border-red-500 focus-within:ring-2 focus-within:ring-red-100 focus-within:shadow-lg'
              }
            `}
            onClick={() => {
              const input = document.getElementById('thai-watsadu-sku');
              input?.focus();
            }}
          >
            <div className="flex items-center gap-2">
              <input
                id="thai-watsadu-sku"
                type="text"
                value={value.sku}
                onChange={(e) => onChange({ ...value, sku: e.target.value })}
                placeholder="e.g., TW-12345-ABC"
                disabled={disabled}
                className={`
                  flex-1 bg-transparent border-none outline-none text-gray-900 placeholder-gray-400 font-medium
                  disabled:cursor-not-allowed disabled:opacity-50
                `}
              />
              {isSkuValid && !errors?.sku && (
                <Check className="w-5 h-5 text-green-600 flex-shrink-0 animate-in zoom-in-50 duration-200" />
              )}
            </div>
          </div>
          {errors?.sku && (
            <p className="text-xs text-red-600 font-medium flex items-center gap-1">
              <span>⚠</span> {errors.sku}
            </p>
          )}
          {!errors?.sku && (
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <Info className="w-3 h-3" />
              Enter the unique product identifier from Thai Watsadu
            </p>
          )}
        </div>

        {/* URL Input */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <label className="block text-sm font-semibold text-gray-900">
              URL <span className="text-red-600">*</span>
            </label>
            <Tooltip content="Paste the full product page URL from Thai Watsadu website" placement="right">
              <Info className="w-4 h-4 text-gray-400 hover:text-gray-600 transition-colors" />
            </Tooltip>
          </div>
          <div
            className={`
              bg-gray-50 rounded-lg px-4 py-3 min-h-[52px] cursor-text border-2 transition-all duration-200
              ${
                errors?.url
                  ? 'border-red-400 ring-2 ring-red-100'
                  : isUrlValid
                  ? 'border-green-400 ring-2 ring-green-100'
                  : 'border-gray-200 hover:border-red-300 focus-within:border-red-500 focus-within:ring-2 focus-within:ring-red-100 focus-within:shadow-lg'
              }
            `}
            onClick={() => {
              const input = document.getElementById('thai-watsadu-url');
              input?.focus();
            }}
          >
            <div className="flex items-center gap-2">
              <input
                id="thai-watsadu-url"
                type="url"
                value={value.url}
                onChange={(e) => onChange({ ...value, url: e.target.value })}
                placeholder="https://www.thaiwatsadu.com/..."
                disabled={disabled}
                className={`
                  flex-1 bg-transparent border-none outline-none text-gray-900 placeholder-gray-400 font-medium
                  disabled:cursor-not-allowed disabled:opacity-50
                `}
              />
              {isUrlValid && !errors?.url && (
                <Check className="w-5 h-5 text-green-600 flex-shrink-0 animate-in zoom-in-50 duration-200" />
              )}
            </div>
          </div>
          {errors?.url && (
            <p className="text-xs text-red-600 font-medium flex items-center gap-1">
              <span>⚠</span> {errors.url}
            </p>
          )}
          {!errors?.url && (
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <Info className="w-3 h-3" />
              Copy and paste the full URL from your browser address bar
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
