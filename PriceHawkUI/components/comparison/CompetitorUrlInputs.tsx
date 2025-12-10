'use client';

import { useState } from 'react';
import { CompetitorRetailer } from '@/lib/types/manual-comparison';
import { COMPETITORS } from '@/lib/constants/competitors';
import { validateCompetitorUrl } from '@/lib/utils/comparison-utils';
import { ChevronDown, ChevronUp, X, ExternalLink } from 'lucide-react';

interface CompetitorUrlInputsProps {
  selectedCompetitors: CompetitorRetailer[];
  competitorUrls: Partial<Record<CompetitorRetailer, string>>;
  onUrlChange: (competitor: CompetitorRetailer, url: string) => void;
  disabled?: boolean;
}

export function CompetitorUrlInputs({
  selectedCompetitors,
  competitorUrls,
  onUrlChange,
  disabled = false,
}: CompetitorUrlInputsProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Partial<Record<CompetitorRetailer, string>>>({});

  const handleUrlChange = (competitor: CompetitorRetailer, url: string) => {
    onUrlChange(competitor, url);

    // Validate URL
    if (url && !validateCompetitorUrl(url, competitor)) {
      setValidationErrors(prev => ({
        ...prev,
        [competitor]: `Invalid URL. Expected domain: ${COMPETITORS[competitor].domain}`,
      }));
    } else {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[competitor];
        return newErrors;
      });
    }
  };

  const handleClear = (competitor: CompetitorRetailer) => {
    onUrlChange(competitor, '');
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[competitor];
      return newErrors;
    });
  };

  if (selectedCompetitors.length === 0) {
    return null;
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="text-left">
          <p className="text-sm font-medium text-gray-700">
            Competitor URLs (Optional)
          </p>
          <p className="text-xs text-gray-500">
            Provide direct URLs for more accurate matching
          </p>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="p-4 space-y-4 bg-white">
          {selectedCompetitors.map((competitorId) => {
            const competitor = COMPETITORS[competitorId];
            const url = competitorUrls[competitorId] || '';
            const error = validationErrors[competitorId];

            return (
              <div key={competitorId} className="space-y-1">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  {competitor.name}
                  <span className="text-xs text-gray-400">({competitor.domain})</span>
                </label>
                <div className="relative">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => handleUrlChange(competitorId, e.target.value)}
                    disabled={disabled}
                    placeholder={`https://${competitor.domain}/product/...`}
                    className={`
                      w-full px-3 py-2 pr-20 border rounded-lg text-sm
                      focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent
                      disabled:bg-gray-100 disabled:cursor-not-allowed
                      ${error ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                    `}
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    {url && (
                      <>
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 text-gray-400 hover:text-sky-600"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                        <button
                          type="button"
                          onClick={() => handleClear(competitorId)}
                          disabled={disabled}
                          className="p-1 text-gray-400 hover:text-red-600 disabled:cursor-not-allowed"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
                {error && (
                  <p className="text-xs text-red-600">{error}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
