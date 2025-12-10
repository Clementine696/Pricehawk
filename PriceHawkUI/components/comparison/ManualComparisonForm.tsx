'use client';

import { useState, useCallback } from 'react';
import Image from 'next/image';
import { SourceProduct, CompetitorRetailer } from '@/lib/types/manual-comparison';
import { detectInputType, validateThaiwatsuduUrl, validateSku } from '@/lib/utils/comparison-utils';
import { CompetitorSelector } from './CompetitorSelector';
import { CompetitorUrlInputs } from './CompetitorUrlInputs';
import { Search, Loader2, AlertCircle, ArrowRight, Package } from 'lucide-react';

interface ManualComparisonFormProps {
  onSubmit: (data: {
    sourceProduct: SourceProduct;
    competitors: CompetitorRetailer[];
    competitorUrls: Partial<Record<CompetitorRetailer, string>>;
  }) => void;
  onFetchProduct: (input: string, inputType: 'sku' | 'url') => Promise<SourceProduct | null>;
  isSubmitting?: boolean;
}

export function ManualComparisonForm({
  onSubmit,
  onFetchProduct,
  isSubmitting = false,
}: ManualComparisonFormProps) {
  const [input, setInput] = useState('');
  const [inputType, setInputType] = useState<'sku' | 'url'>('sku');
  const [selectedCompetitors, setSelectedCompetitors] = useState<CompetitorRetailer[]>([
    'HOMEPRO', 'MEGA_HOME', 'BOONTHAVORN', 'GLOBAL_HOUSE', 'DOHOME'
  ]);
  const [competitorUrls, setCompetitorUrls] = useState<Partial<Record<CompetitorRetailer, string>>>({});
  const [sourceProduct, setSourceProduct] = useState<SourceProduct | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (value: string) => {
    setInput(value);
    setInputType(detectInputType(value));
    setError(null);
    // Clear source product when input changes
    if (sourceProduct) {
      setSourceProduct(null);
    }
  };

  const validateInput = (): boolean => {
    if (!input.trim()) {
      setError('Please enter a SKU or URL');
      return false;
    }

    if (inputType === 'url') {
      if (!validateThaiwatsuduUrl(input)) {
        setError('Please enter a valid Thaiwatsadu URL');
        return false;
      }
    } else {
      if (!validateSku(input)) {
        setError('Please enter a valid SKU (3-20 alphanumeric characters)');
        return false;
      }
    }

    return true;
  };

  const handleFetchProduct = async () => {
    if (!validateInput()) return;

    setIsFetching(true);
    setError(null);

    try {
      const product = await onFetchProduct(input, inputType);
      if (product) {
        setSourceProduct(product);
      } else {
        setError('Product not found. Please check the SKU or URL.');
      }
    } catch (err) {
      setError('Failed to fetch product information. Please try again.');
    } finally {
      setIsFetching(false);
    }
  };

  const handleCompetitorUrlChange = (competitor: CompetitorRetailer, url: string) => {
    setCompetitorUrls(prev => ({
      ...prev,
      [competitor]: url,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!sourceProduct) {
      setError('Please fetch product information first');
      return;
    }

    if (selectedCompetitors.length === 0) {
      setError('Please select at least one competitor');
      return;
    }

    onSubmit({
      sourceProduct,
      competitors: selectedCompetitors,
      competitorUrls,
    });
  };

  const canSubmit = sourceProduct && selectedCompetitors.length > 0 && !isSubmitting;

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Input Section</h2>

      {/* Thaiwatsadu Product Input */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Thaiwatsadu Product
        </label>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => handleInputChange(e.target.value)}
              placeholder="Enter SKU (e.g., 1145439) or URL"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              disabled={isFetching || isSubmitting}
            />
            {input && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 uppercase">
                {inputType}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={handleFetchProduct}
            disabled={isFetching || isSubmitting || !input.trim()}
            className="flex items-center gap-2 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isFetching ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            <span>Fetch Info</span>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Source Product Preview */}
        {sourceProduct && (
          <div className="mt-3 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start gap-4">
              <div className="relative w-16 h-16 bg-white rounded-lg overflow-hidden flex-shrink-0">
                {sourceProduct.imageUrl ? (
                  <Image
                    src={sourceProduct.imageUrl}
                    alt={sourceProduct.name}
                    fill
                    className="object-cover"
                    sizes="64px"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Package className="w-8 h-8 text-gray-300" />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{sourceProduct.name}</p>
                <p className="text-sm text-gray-600">SKU: {sourceProduct.sku}</p>
                <p className="text-sm font-medium text-sky-600">฿{sourceProduct.price.toLocaleString()}</p>
              </div>
              <div className="flex items-center text-green-600">
                <span className="text-sm font-medium">Product Found</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Competitor Selection */}
      <CompetitorSelector
        selectedCompetitors={selectedCompetitors}
        onSelectionChange={setSelectedCompetitors}
        disabled={isSubmitting}
      />

      {/* Optional Competitor URLs */}
      <CompetitorUrlInputs
        selectedCompetitors={selectedCompetitors}
        competitorUrls={competitorUrls}
        onUrlChange={handleCompetitorUrlChange}
        disabled={isSubmitting}
      />

      {/* Submit Button */}
      <div className="flex justify-end pt-4 border-t border-gray-100">
        <button
          type="submit"
          disabled={!canSubmit}
          className="flex items-center gap-2 px-6 py-2.5 bg-sky-500 text-white rounded-lg hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <span>Compare Products</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </form>
  );
}
