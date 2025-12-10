'use client';

import { CompetitorMatchResult } from '@/lib/types/manual-comparison';
import { CheckCircle, RefreshCw, Download, Loader2 } from 'lucide-react';

interface ComparisonResultActionsProps {
  results: CompetitorMatchResult[];
  onConfirmAll: () => void;
  onRetryFailed: () => void;
  onExport: () => void;
  isProcessing?: boolean;
}

export function ComparisonResultActions({
  results,
  onConfirmAll,
  onRetryFailed,
  onExport,
  isProcessing = false,
}: ComparisonResultActionsProps) {
  // Calculate statistics
  const totalResults = results.length;
  const matchedCount = results.filter(r => r.status === 'match').length;
  const notMatchedCount = results.filter(r => r.status === 'not_match').length;
  const errorCount = results.filter(r => r.status === 'error').length;
  const pendingCount = results.filter(r => r.status === 'pending').length;
  const verifiedCount = results.filter(r => r.userVerified !== undefined).length;
  const unverifiedMatches = results.filter(r => r.status === 'match' && r.userVerified === undefined).length;
  const failedOrNotMatched = results.filter(r => r.status === 'not_match' || r.status === 'error').length;

  const hasUnverifiedMatches = unverifiedMatches > 0;
  const hasFailedResults = failedOrNotMatched > 0;
  const hasPendingResults = pendingCount > 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      {/* Statistics Summary */}
      <div className="flex flex-wrap gap-4 mb-4 pb-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Total:</span>
          <span className="font-medium text-gray-900">{totalResults}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-sm text-gray-500">Matched:</span>
          <span className="font-medium text-green-600">{matchedCount}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500" />
          <span className="text-sm text-gray-500">Not Matched:</span>
          <span className="font-medium text-red-600">{notMatchedCount}</span>
        </div>
        {errorCount > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-orange-500" />
            <span className="text-sm text-gray-500">Errors:</span>
            <span className="font-medium text-orange-600">{errorCount}</span>
          </div>
        )}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Verified:</span>
          <span className="font-medium text-sky-600">{verifiedCount}/{totalResults}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Confirm All Matches */}
        <button
          type="button"
          onClick={onConfirmAll}
          disabled={isProcessing || !hasUnverifiedMatches || hasPendingResults}
          className="flex items-center gap-2 px-4 py-2 bg-sky-500 text-white rounded-lg hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isProcessing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <CheckCircle className="w-4 h-4" />
          )}
          <span className="font-medium">Confirm All Matches</span>
          {hasUnverifiedMatches && (
            <span className="px-1.5 py-0.5 text-xs bg-sky-400 rounded">
              {unverifiedMatches}
            </span>
          )}
        </button>

        {/* Retry Failed */}
        <button
          type="button"
          onClick={onRetryFailed}
          disabled={isProcessing || !hasFailedResults || hasPendingResults}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isProcessing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          <span className="font-medium">Retry Failed</span>
          {hasFailedResults && (
            <span className="px-1.5 py-0.5 text-xs bg-gray-200 rounded">
              {failedOrNotMatched}
            </span>
          )}
        </button>

        {/* Export Results */}
        <button
          type="button"
          onClick={onExport}
          disabled={isProcessing || hasPendingResults || totalResults === 0}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ml-auto"
        >
          <Download className="w-4 h-4" />
          <span className="font-medium">Export Results</span>
        </button>
      </div>

      {/* Processing Message */}
      {hasPendingResults && (
        <p className="mt-3 text-sm text-amber-600 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin" />
          Processing comparisons... Please wait.
        </p>
      )}
    </div>
  );
}
