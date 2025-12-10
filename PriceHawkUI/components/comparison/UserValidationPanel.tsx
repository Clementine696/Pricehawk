'use client';

import { CompetitorMatchResult } from '@/lib/types/manual-comparison';
import { COMPETITORS } from '@/lib/constants/competitors';
import { RefreshCw, Check, Loader2, AlertCircle, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { EmptyState } from './EmptyState';
import Image from 'next/image';

interface UserValidationPanelProps {
  results: CompetitorMatchResult[];
  onRetry: () => void;
  onConfirm: () => void;
  isProcessing?: boolean;
}

export function UserValidationPanel({
  results,
  onRetry,
  onConfirm,
  isProcessing = false,
}: UserValidationPanelProps) {
  const hasPending = results.some((r) => r.status === 'pending');

  // Group results by status
  const matchResults = results.filter(r => r.status === 'match');
  const partialResults = results.filter(r => {
    const matchCount = r.matchCount ?? 0;
    const notMatchCount = r.notMatchCount ?? 0;
    return matchCount > 0 && notMatchCount > 0;
  });
  const noMatchResults = results.filter(r => r.status === 'not_match');
  const errorResults = results.filter(r => r.status === 'error');

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900">Validation Results</h3>
        <p className="text-xs text-gray-500 mt-1">Review the match results below</p>
      </div>

      {/* Results List */}
      <div className="p-4 space-y-3">
        {results.length === 0 ? (
          <EmptyState
            icon={AlertCircle}
            title="No results yet"
            description="Click Compare to process the comparison and see the results here."
          />
        ) : (
          <>
            {/* Matches */}
            {matchResults.length > 0 && (
              <div className="space-y-2">
                {matchResults.map((result) => (
                  <CompetitorValidationRow key={result.competitor} result={result} />
                ))}
              </div>
            )}

            {/* Partial Matches */}
            {partialResults.length > 0 && (
              <div className="space-y-2">
                {partialResults.map((result) => (
                  <CompetitorValidationRow key={result.competitor} result={result} />
                ))}
              </div>
            )}

            {/* No Matches */}
            {noMatchResults.length > 0 && (
              <div className="space-y-2">
                {noMatchResults.map((result) => (
                  <CompetitorValidationRow key={result.competitor} result={result} />
                ))}
              </div>
            )}

            {/* Errors */}
            {errorResults.length > 0 && (
              <div className="space-y-2">
                {errorResults.map((result) => (
                  <CompetitorValidationRow key={result.competitor} result={result} />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Action Guidance */}
      {results.length > 0 && !hasPending && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            {matchResults.length > 0 || partialResults.length > 0
              ? '✓ Review matches and click Confirm to proceed'
              : '✗ No matches found. Try different URLs or Retry'}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="p-4 border-t border-gray-200 flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={onRetry}
          disabled={isProcessing || hasPending}
          className="flex items-center gap-2 px-6 py-2.5 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isProcessing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          <span>Retry</span>
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isProcessing || hasPending}
          className="flex items-center gap-2 px-8 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
        >
          {isProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Check className="w-5 h-5" />
          )}
          <span>Confirm</span>
        </button>
      </div>
    </div>
  );
}

interface CompetitorValidationRowProps {
  result: CompetitorMatchResult;
}

function CompetitorValidationRow({ result }: CompetitorValidationRowProps) {
  const competitor = COMPETITORS[result.competitor];
  const matchCount = result.matchCount ?? (result.status === 'match' ? 1 : 0);
  const notMatchCount = result.notMatchCount ?? (result.status === 'not_match' ? 1 : 0);
  const totalUrls = matchCount + notMatchCount;
  const isPending = result.status === 'pending';
  const isPartial = matchCount > 0 && notMatchCount > 0;

  // Determine overall status
  const getStatusInfo = () => {
    if (isPending) {
      return {
        icon: Loader2,
        text: 'Processing...',
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-700',
        iconColor: 'text-gray-400',
      };
    }
    if (result.status === 'error') {
      return {
        icon: AlertCircle,
        text: 'Error',
        bgColor: 'bg-red-100',
        textColor: 'text-red-800',
        iconColor: 'text-red-600',
      };
    }
    if (result.status === 'not_match' || (totalUrls > 0 && matchCount === 0)) {
      return {
        icon: XCircle,
        text: 'No match found',
        bgColor: 'bg-red-100',
        textColor: 'text-red-800',
        iconColor: 'text-red-600',
      };
    }
    if (isPartial) {
      return {
        icon: AlertTriangle,
        text: `${matchCount} of ${totalUrls} matched`,
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-800',
        iconColor: 'text-yellow-600',
      };
    }
    return {
      icon: CheckCircle,
      text: `Match found (${result.confidence}% confidence)`,
      bgColor: 'bg-green-100',
      textColor: 'text-green-800',
      iconColor: 'text-green-600',
    };
  };

  const statusInfo = getStatusInfo();
  const StatusIcon = statusInfo.icon;

  return (
    <div className="border-2 border-gray-200 rounded-lg overflow-hidden hover:shadow-sm transition-shadow">
      {/* Competitor Header */}
      <div
        className="px-4 py-2 flex items-center gap-2"
        style={{ backgroundColor: competitor.color }}
      >
        {competitor.logo && (
          <Image
            src={competitor.logo}
            alt={competitor.name}
            width={24}
            height={24}
            className="object-contain"
          />
        )}
        <span className="text-sm font-semibold text-white">{competitor.name}</span>
      </div>

      {/* Results Content */}
      <div className="bg-white p-4">
        {isPending ? (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
            <span className="ml-2 text-sm text-gray-500">Processing...</span>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Status Badge */}
            <div
              className={`flex items-center gap-2 px-3 py-2 rounded-lg ${statusInfo.bgColor}`}
            >
              <StatusIcon className={`w-5 h-5 flex-shrink-0 ${statusInfo.iconColor} ${isPending ? 'animate-spin' : ''}`} />
              <span className={`text-sm font-semibold ${statusInfo.textColor}`}>
                {statusInfo.text}
              </span>
            </div>

            {/* Detailed Results for Partial Matches */}
            {isPartial && totalUrls > 0 && (
              <div className="space-y-2 pt-2 border-t border-gray-200">
                {matchCount > 0 && (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-sm text-gray-700">
                      {matchCount} {matchCount === 1 ? 'URL' : 'URLs'} matched
                    </span>
                  </div>
                )}
                {notMatchCount > 0 && (
                  <div className="flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-red-600" />
                    <span className="text-sm text-gray-700">
                      {notMatchCount} {notMatchCount === 1 ? 'URL' : 'URLs'} not matched
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Error Message */}
            {result.status === 'error' && result.errorMessage && (
              <div className="text-sm text-red-600 pt-2 border-t border-gray-200">
                {result.errorMessage}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
