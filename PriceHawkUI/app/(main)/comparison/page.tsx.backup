'use client';

import { useState, useCallback } from 'react';
import {
  ThaiWatsuduInput,
  CompetitorRetailer,
  CompetitorUrlEntry,
  CompetitorMatchResult,
  ManualComparisonResponse,
} from '@/lib/types/manual-comparison';
import {
  ThaiWatsuduInputCard,
  RetailerSelector,
  CompetitorInputCard,
  UserValidationPanel,
} from '@/components/comparison';
import { StageIndicator } from '@/components/comparison/StageIndicator';
import { Toast, ToastVariant } from '@/components/ui/Toast';
import { LoadingOverlay } from '@/components/comparison/LoadingOverlay';
import { MainLayout } from '@/components/layout/MainLayout';
import { ArrowRight, ChevronLeft, Loader2 } from 'lucide-react';

// Stage type for the 4-stage flow
type ComparisonStage = 'input' | 'selecting' | 'competitor_urls' | 'validation';

// Validation error types
interface ValidationErrors {
  thaiWatsadu?: {
    sku?: string;
    url?: string;
  };
  retailers?: string;
  competitorUrls?: Record<string, string>;
}

export default function ManualComparisonPage() {
  // Stage management
  const [stage, setStage] = useState<ComparisonStage>('input');

  // Form state
  const [thaiWatsuduInput, setThaiWatsuduInput] = useState<ThaiWatsuduInput>({
    sku: '',
    url: '',
  });
  const [selectedRetailers, setSelectedRetailers] = useState<CompetitorRetailer[]>([]);
  const [competitorEntries, setCompetitorEntries] = useState<CompetitorUrlEntry[]>([]);

  // Results state
  const [results, setResults] = useState<CompetitorMatchResult[]>([]);
  const [comparisonId, setComparisonId] = useState<string | null>(null);

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [toast, setToast] = useState<{
    isVisible: boolean;
    message: string;
    variant: ToastVariant;
  }>({
    isVisible: false,
    message: '',
    variant: 'success',
  });

  // Toggle retailer selection
  const handleRetailerSelect = useCallback((retailer: CompetitorRetailer) => {
    setSelectedRetailers((prev) => {
      if (prev.includes(retailer)) {
        return prev.filter((r) => r !== retailer);
      }
      return [...prev, retailer];
    });
  }, []);

  // Validate Stage 1: Thai Watsadu input
  const validateThaiWatsuduInput = useCallback((): boolean => {
    const newErrors: ValidationErrors = {};

    if (!thaiWatsuduInput.sku.trim()) {
      newErrors.thaiWatsadu = { ...newErrors.thaiWatsadu, sku: 'SKU is required' };
    }

    if (!thaiWatsuduInput.url.trim()) {
      newErrors.thaiWatsadu = { ...newErrors.thaiWatsadu, url: 'URL is required' };
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [thaiWatsuduInput]);

  // Validate Stage 2: Retailer selection
  const validateRetailerSelection = useCallback((): boolean => {
    if (selectedRetailers.length === 0) {
      setErrors({ retailers: 'Please select at least one retailer' });
      return false;
    }
    setErrors({});
    return true;
  }, [selectedRetailers]);

  // Validate Stage 3: Competitor URLs
  const validateCompetitorUrls = useCallback((): boolean => {
    const urlErrors: Record<string, string> = {};

    competitorEntries.forEach((entry) => {
      const validUrls = entry.urls.filter((url) => url.trim() !== '');
      if (validUrls.length === 0) {
        urlErrors[entry.id] = 'At least one URL is required';
      }
    });

    if (Object.keys(urlErrors).length > 0) {
      setErrors({ competitorUrls: urlErrors });
      return false;
    }

    setErrors({});
    return true;
  }, [competitorEntries]);

  // Handle Stage 1 -> Stage 2 transition
  const handleGoToRetailerSelection = useCallback(() => {
    if (validateThaiWatsuduInput()) {
      setStage('selecting');
    }
  }, [validateThaiWatsuduInput]);

  // Handle Stage 2 -> Stage 3 transition
  const handleGoToCompetitorUrls = useCallback(() => {
    if (validateRetailerSelection()) {
      // Initialize competitor entries for selected retailers
      const entries: CompetitorUrlEntry[] = selectedRetailers.map((retailer) => ({
        id: `${retailer}-${Date.now()}`,
        retailer,
        urls: [''], // Start with one empty URL field
      }));
      setCompetitorEntries(entries);
      setStage('competitor_urls');
    }
  }, [selectedRetailers, validateRetailerSelection]);

  // Handle competitor entry update
  const handleCompetitorEntryChange = useCallback((updatedEntry: CompetitorUrlEntry) => {
    setCompetitorEntries((prev) =>
      prev.map((entry) => (entry.id === updatedEntry.id ? updatedEntry : entry))
    );
  }, []);

  // Handle competitor entry removal
  const handleCompetitorEntryRemove = useCallback((entryId: string) => {
    setCompetitorEntries((prev) => prev.filter((entry) => entry.id !== entryId));
    setSelectedRetailers((prev) => {
      const entry = competitorEntries.find((e) => e.id === entryId);
      if (entry) {
        return prev.filter((r) => r !== entry.retailer);
      }
      return prev;
    });
  }, [competitorEntries]);

  // Submit comparison
  const handleSubmitComparison = useCallback(async () => {
    if (!validateCompetitorUrls()) return;

    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await fetch('/api/comparison/manual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          thaiWatsadu: thaiWatsuduInput,
          competitors: competitorEntries,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process comparison');
      }

      const result: ManualComparisonResponse = await response.json();

      setResults(result.results);
      setComparisonId(result.id);
      setStage('validation');
    } catch (err) {
      console.error('Error submitting comparison:', err);
      setToast({
        isVisible: true,
        message: 'Failed to process comparison. Please try again.',
        variant: 'error',
      });
      setErrors({ retailers: 'Failed to process comparison. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  }, [thaiWatsuduInput, competitorEntries, validateCompetitorUrls]);

  // Handle Retry
  const handleRetry = useCallback(async () => {
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/comparison/manual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          thaiWatsadu: thaiWatsuduInput,
          competitors: competitorEntries,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to retry comparison');
      }

      const result: ManualComparisonResponse = await response.json();
      setResults(result.results);
      setComparisonId(result.id);
    } catch (err) {
      console.error('Error retrying comparison:', err);
    } finally {
      setIsSubmitting(false);
    }
  }, [thaiWatsuduInput, competitorEntries]);

  // Handle Confirm
  const handleConfirm = useCallback(() => {
    // In a real app, this would save the confirmed results
    console.log('Confirmed comparison:', {
      id: comparisonId,
      thaiWatsadu: thaiWatsuduInput,
      results,
    });

    // Show success toast
    setToast({
      isVisible: true,
      message: 'Comparison confirmed successfully!',
      variant: 'success',
    });

    // Reset to start a new comparison after a short delay
    setTimeout(() => {
      setStage('input');
      setThaiWatsuduInput({ sku: '', url: '' });
      setSelectedRetailers([]);
      setCompetitorEntries([]);
      setResults([]);
      setComparisonId(null);
    }, 500);
  }, [comparisonId, thaiWatsuduInput, results]);

  // Go back to previous stage
  const handleBack = useCallback(() => {
    switch (stage) {
      case 'selecting':
        setStage('input');
        break;
      case 'competitor_urls':
        setStage('selecting');
        break;
      case 'validation':
        setStage('competitor_urls');
        break;
    }
  }, [stage]);

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Breadcrumb */}
        <nav className="text-sm text-gray-500">
          <span>Home</span>
          <span className="mx-2">/</span>
          <span className="text-gray-900 font-medium">Manual Comparison</span>
        </nav>

        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Manual Comparison</h1>
          <p className="text-gray-600 mt-1">Compare products across retailers manually</p>
        </div>

        {/* Stage Indicator */}
        <StageIndicator currentStage={stage} />

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Thai Watsadu + Retailer Selection */}
        <div className="space-y-6">
          {/* Stage 1: Thai Watsadu Input */}
          <div className={stage === 'input' ? '' : 'opacity-60'}>
            <ThaiWatsuduInputCard
              value={thaiWatsuduInput}
              onChange={setThaiWatsuduInput}
              disabled={stage !== 'input'}
              errors={errors.thaiWatsadu}
            />

            {stage === 'input' && (
              <div className="mt-4 flex justify-end">
                <button
                  type="button"
                  onClick={handleGoToRetailerSelection}
                  className="px-6 py-2.5 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 shadow-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </div>

          {/* Arrow between Thai Watsadu and Retailer Selection */}
          {(stage === 'selecting' || stage === 'competitor_urls' || stage === 'validation') && (
            <div className="flex justify-center">
              <ArrowRight className="w-6 h-6 text-amber-500 rotate-90" />
            </div>
          )}

          {/* Stage 2: Retailer Selection */}
          {(stage === 'selecting' || stage === 'competitor_urls' || stage === 'validation') && (
            <div className={stage === 'selecting' ? '' : 'opacity-60'}>
              <RetailerSelector
                selectedRetailers={selectedRetailers}
                onSelect={handleRetailerSelect}
                disabled={stage !== 'selecting'}
              />

              {errors.retailers && stage === 'selecting' && (
                <p className="mt-2 text-sm text-red-600">{errors.retailers}</p>
              )}

              {stage === 'selecting' && (
                <div className="mt-4 flex justify-between">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="flex items-center gap-2 px-4 py-2.5 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg font-medium transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Back</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleGoToCompetitorUrls}
                    className="px-6 py-2.5 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 shadow-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Competitor Inputs + Validation */}
        <div className="space-y-6">
          {/* Stage 3: Competitor URL Inputs */}
          {(stage === 'competitor_urls' || stage === 'validation') && (
            <div className={stage === 'competitor_urls' ? '' : 'opacity-60'}>
              <div className="space-y-4">
                {competitorEntries.map((entry) => (
                  <CompetitorInputCard
                    key={entry.id}
                    entry={entry}
                    onChange={handleCompetitorEntryChange}
                    onRemove={() => handleCompetitorEntryRemove(entry.id)}
                    disabled={stage !== 'competitor_urls' || isSubmitting}
                    error={errors.competitorUrls?.[entry.id]}
                  />
                ))}
              </div>

              {stage === 'competitor_urls' && (
                <div className="mt-4 flex justify-between">
                  <button
                    type="button"
                    onClick={handleBack}
                    disabled={isSubmitting}
                    className="flex items-center gap-2 px-4 py-2.5 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Back</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleSubmitComparison}
                    disabled={isSubmitting || competitorEntries.length === 0}
                    className="flex items-center gap-2 px-6 py-2.5 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 shadow-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    <span>Compare</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Arrow between Competitor Inputs and Validation */}
          {stage === 'validation' && (
            <div className="flex justify-center">
              <ArrowRight className="w-6 h-6 text-amber-500 rotate-90" />
            </div>
          )}

          {/* Stage 4: User Validation */}
          {stage === 'validation' && (
            <UserValidationPanel
              results={results}
              onRetry={handleRetry}
              onConfirm={handleConfirm}
              isProcessing={isSubmitting}
            />
          )}
        </div>
      </div>

      {/* Comparison ID (shown in validation stage) */}
      {stage === 'validation' && comparisonId && (
        <p className="text-xs text-gray-400 text-center">
          Comparison ID: {comparisonId}
        </p>
      )}
      </div>

      {/* Loading Overlay */}
      {isSubmitting && <LoadingOverlay message="Processing comparison..." />}

      {/* Toast Notification */}
      <Toast
        message={toast.message}
        variant={toast.variant}
        isVisible={toast.isVisible}
        onClose={() => setToast({ ...toast, isVisible: false })}
      />
    </MainLayout>
  );
}
