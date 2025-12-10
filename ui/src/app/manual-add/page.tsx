'use client';

import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Plus, RotateCcw, Check, X, ExternalLink, Info, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { apiFetch } from '@/lib/api';

// Types
type ComparisonStage = 'input' | 'review' | 'scraping' | 'results';

interface ScrapedProduct {
  name: string | null;
  retailer: string | null;
  url: string | null;
  source_url: string | null;
  current_price: number | null;
  original_price: number | null;
  brand: string | null;
  sku: string | null;
  category: string | null;
  images: string[];
  has_discount: boolean;
  discount_percent: number | null;
}

interface ScrapeError {
  url: string;
  error: string;
}

interface ThaiWatsuduInput {
  sku: string;
  url: string;
}

interface CompetitorEntry {
  id: string;
  retailer: string;
  url: string;
}

// Competitor configuration (matching PriceHawkUI)
const COMPETITORS = [
  { id: 'HomePro', name: 'HomePro', nameTh: 'โฮมโปร', color: '#1E88E5', domain: 'homepro.co.th', logo: '/logos/homepro.png', retailerId: 'hp' },
  { id: 'MegaHome', name: 'MegaHome', nameTh: 'เมกาโฮม', color: '#43A047', domain: 'megahome.co.th', logo: '/logos/megahome.png', retailerId: 'mgh' },
  { id: 'Boonthavorn', name: 'Boonthavorn', nameTh: 'บุญถาวร', color: '#7B1FA2', domain: 'boonthavorn.com', logo: '/logos/boonthavorn.png', retailerId: 'btv' },
  { id: 'Global House', name: 'Global House', nameTh: 'โกลบอลเฮ้าส์', color: '#F57C00', domain: 'globalhouse.co.th', logo: '/logos/globalhouse.png', retailerId: 'gbh' },
  { id: 'Do Home', name: 'DoHome', nameTh: 'ดูโฮม', color: '#E64A19', domain: 'dohome.co.th', logo: '/logos/dohome.png', retailerId: 'dh' },
];

interface ExistingMatch {
  retailer_id: string;
  retailer_name: string;
  product_id: number;
  sku: string;
  name: string;
  price: number | null;
}

const THAI_WATSADU_COLOR = '#DC2626';

// Stage Indicator Component
function StageIndicator({ currentStage }: { currentStage: ComparisonStage }) {
  const stages = [
    { id: 'input', label: 'Input', number: 1 },
    { id: 'review', label: 'Review', number: 2 },
    { id: 'scraping', label: 'Scraping', number: 3 },
    { id: 'results', label: 'Results', number: 4 },
  ];

  const currentIndex = stages.findIndex(s => s.id === currentStage);

  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between max-w-2xl mx-auto px-4">
        {stages.map((stage, index) => {
          const isActive = stage.id === currentStage;
          const isCompleted = index < currentIndex;
          const isLast = index === stages.length - 1;

          return (
            <div key={stage.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center relative">
                <div
                  className={`
                    w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300
                    ${isActive
                      ? 'bg-gradient-to-br from-cyan-500 to-cyan-600 text-white shadow-lg scale-110 ring-2 ring-cyan-400 ring-offset-2'
                      : isCompleted
                      ? 'bg-cyan-500 text-white shadow-md'
                      : 'bg-gray-200 text-gray-400'
                    }
                  `}
                >
                  {isCompleted ? <Check className="w-5 h-5" /> : stage.number}
                </div>
                <span className={`mt-2 text-sm font-medium ${isActive ? 'text-cyan-600' : 'text-gray-500'}`}>
                  {stage.label}
                </span>
              </div>
              {!isLast && (
                <div className={`flex-1 h-1 mx-4 rounded ${index < currentIndex ? 'bg-cyan-500' : 'bg-gray-200'}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Competitor Input Card Component
function CompetitorInputCard({
  id,
  retailer,
  url,
  onRetailerChange,
  onUrlChange,
  onRemove,
  error,
  usedRetailers,
  alreadyMatchedRetailers = [],
}: {
  id: string;
  retailer: string;
  url: string;
  onRetailerChange: (retailer: string) => void;
  onUrlChange: (url: string) => void;
  onRemove: () => void;
  error?: string;
  usedRetailers: string[];
  alreadyMatchedRetailers?: string[];
}) {
  const [showRetailerSelector, setShowRetailerSelector] = useState(!retailer);
  const selectedCompetitor = COMPETITORS.find(c => c.id === retailer);
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
          className="rounded p-1 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Form Fields */}
      <div className="space-y-4 p-4">
        {/* Retailer Selection */}
        <div>
          <div className="mb-3 flex items-center gap-2">
            <label className="block text-sm font-semibold text-gray-900">
              Select Retailer {!retailer && <span className="text-red-600">*</span>}
            </label>
            <Info className="w-4 h-4 text-gray-400" />
          </div>

          {/* Selected Retailer Display */}
          {retailer && !showRetailerSelector && (
            <button
              type="button"
              onClick={() => setShowRetailerSelector(true)}
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

          {/* Retailer Selection Grid */}
          {(!retailer || showRetailerSelector) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {COMPETITORS.map((comp) => {
                const isUsed = usedRetailers.includes(comp.id);
                const isCurrentSelection = retailer === comp.id;
                const isAlreadyMatched = alreadyMatchedRetailers.includes(comp.retailerId);
                const isDisabled = (isUsed && !isCurrentSelection) || isAlreadyMatched;

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
                      ${isCurrentSelection
                        ? 'shadow-lg scale-[1.02]'
                        : isDisabled
                        ? 'opacity-50 cursor-not-allowed'
                        : 'hover:shadow-md hover:scale-[1.02] cursor-pointer'
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
                        <Check className="w-5 h-5 flex-shrink-0" style={{ color: comp.color }} />
                      )}
                    </div>
                    {isAlreadyMatched && (
                      <div className="absolute top-2 right-2">
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          Matched
                        </span>
                      </div>
                    )}
                    {isUsed && !isCurrentSelection && !isAlreadyMatched && (
                      <div className="absolute top-2 right-2">
                        <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">Used</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Product URL Input */}
        <div>
          <div className="mb-2 flex items-center gap-2">
            <label className="block text-sm font-semibold text-gray-900">
              Product URL {retailer && <span className="text-red-600">*</span>}
            </label>
            <Info className="w-4 h-4 text-gray-400" />
          </div>
          <div
            className={`
              min-h-[52px] rounded-lg border-2 bg-gray-50 px-4 py-3 transition-all duration-200
              ${error
                ? 'border-red-400 ring-2 ring-red-100'
                : isUrlValid && retailer
                ? 'border-green-400 ring-2 ring-green-100'
                : 'border-gray-200 hover:border-gray-300 focus-within:border-cyan-500 focus-within:ring-2 focus-within:ring-cyan-100'
              }
              ${!retailer ? 'opacity-50' : ''}
            `}
          >
            <div className="flex items-center gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => onUrlChange(e.target.value)}
                placeholder={selectedCompetitor ? `https://www.${selectedCompetitor.domain}/...` : 'Select a retailer first'}
                disabled={!retailer}
                className="flex-1 border-none bg-transparent font-medium text-gray-900 outline-none placeholder-gray-400 disabled:cursor-not-allowed disabled:opacity-50"
              />
              {isUrlValid && retailer && !error && (
                <Check className="w-5 h-5 text-green-600 flex-shrink-0" />
              )}
            </div>
          </div>
          {error ? (
            <p className="mt-1 text-xs font-medium text-red-600">⚠ {error}</p>
          ) : retailer ? (
            <p className="mt-1 text-xs text-gray-500 flex items-center gap-1">
              <Info className="w-3 h-3" />
              Copy and paste the full URL from {selectedCompetitor?.name} website
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default function ManualAddPage() {
  const searchParams = useSearchParams();

  // Stage management
  const [stage, setStage] = useState<ComparisonStage>('input');

  // Form state
  const [thaiWatsuduInput, setThaiWatsuduInput] = useState<ThaiWatsuduInput>({ sku: '', url: '' });
  const [competitorEntries, setCompetitorEntries] = useState<CompetitorEntry[]>([
    { id: `competitor-${Date.now()}`, retailer: '', url: '' },
  ]);

  // Pre-fill from query parameters (when navigating from Product Detail page)
  useEffect(() => {
    const skuParam = searchParams.get('sku');
    const urlParam = searchParams.get('url');
    const retailerParam = searchParams.get('retailer');

    if (skuParam || urlParam) {
      setThaiWatsuduInput({
        sku: skuParam || '',
        url: urlParam || '',
      });
    }

    // Pre-select retailer if specified
    if (retailerParam) {
      const competitor = COMPETITORS.find(c => c.retailerId === retailerParam);
      if (competitor) {
        setCompetitorEntries([
          { id: `competitor-${Date.now()}`, retailer: competitor.id, url: '' },
        ]);
      }
    }
  }, [searchParams]);

  // Results state
  const [comparisonResult, setComparisonResult] = useState<any>(null);

  // Scraping state
  const [scrapedProducts, setScrapedProducts] = useState<ScrapedProduct[]>([]);
  const [scrapeErrors, setScrapeErrors] = useState<ScrapeError[]>([]);
  const [scrapeProgress, setScrapeProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });
  const [isScraping, setIsScraping] = useState(false);

  // Existing matches state
  const [existingMatches, setExistingMatches] = useState<ExistingMatch[]>([]);
  const [verifiedRetailers, setVerifiedRetailers] = useState<string[]>([]);
  const [productFound, setProductFound] = useState<boolean | null>(null);
  const [isCheckingMatches, setIsCheckingMatches] = useState(false);

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    thaiWatsadu?: { sku?: string; url?: string };
    competitors?: Record<string, string>;
    general?: string;
  }>({});

  // Validation helpers
  const isSkuValid = thaiWatsuduInput.sku.trim().length > 0;
  const isUrlValid = thaiWatsuduInput.url.trim().length > 0 && thaiWatsuduInput.url.startsWith('http');

  // Fetch existing matches when SKU changes
  useEffect(() => {
    const fetchExistingMatches = async () => {
      const sku = thaiWatsuduInput.sku.trim();
      if (sku.length < 3) {
        setExistingMatches([]);
        setVerifiedRetailers([]);
        setProductFound(null);
        return;
      }

      setIsCheckingMatches(true);
      try {
        const response = await apiFetch(`/api/products/sku/${encodeURIComponent(sku)}/matches`);
        if (response.ok) {
          const data = await response.json();
          setProductFound(data.found);
          setVerifiedRetailers(data.verified_retailers || []);
          setExistingMatches(data.matches || []);
        }
      } catch (error) {
        console.error('Error fetching existing matches:', error);
      } finally {
        setIsCheckingMatches(false);
      }
    };

    const debounceTimer = setTimeout(fetchExistingMatches, 500);
    return () => clearTimeout(debounceTimer);
  }, [thaiWatsuduInput.sku]);

  // Add competitor
  const handleAddCompetitor = useCallback(() => {
    setCompetitorEntries((prev) => [
      ...prev,
      { id: `competitor-${Date.now()}-${Math.random()}`, retailer: '', url: '' },
    ]);
  }, []);

  // Remove competitor
  const handleRemoveCompetitor = useCallback((id: string) => {
    setCompetitorEntries((prev) => prev.filter((entry) => entry.id !== id));
  }, []);

  // Update competitor retailer
  const handleCompetitorRetailerChange = useCallback((id: string, retailer: string) => {
    setCompetitorEntries((prev) =>
      prev.map((entry) => (entry.id === id ? { ...entry, retailer } : entry))
    );
  }, []);

  // Update competitor URL
  const handleCompetitorUrlChange = useCallback((id: string, url: string) => {
    setCompetitorEntries((prev) =>
      prev.map((entry) => (entry.id === id ? { ...entry, url } : entry))
    );
  }, []);

  // Get used retailers
  const getUsedRetailers = useCallback((): string[] => {
    return competitorEntries.map((entry) => entry.retailer).filter((r) => r !== '');
  }, [competitorEntries]);

  // Validate input stage
  const validateInputStage = useCallback((): boolean => {
    const newErrors: typeof errors = {};

    if (!thaiWatsuduInput.sku.trim()) {
      newErrors.thaiWatsadu = { ...newErrors.thaiWatsadu, sku: 'SKU is required' };
    }
    if (!thaiWatsuduInput.url.trim()) {
      newErrors.thaiWatsadu = { ...newErrors.thaiWatsadu, url: 'URL is required' };
    }

    const competitorErrors: Record<string, string> = {};
    let hasAtLeastOneCompetitor = false;

    competitorEntries.forEach((entry) => {
      if (entry.retailer && entry.url.trim()) {
        hasAtLeastOneCompetitor = true;
      }
      if (entry.retailer && !entry.url.trim()) {
        competitorErrors[entry.id] = 'URL is required';
      }
      if (!entry.retailer && entry.url.trim()) {
        competitorErrors[entry.id] = 'Retailer selection is required';
      }
    });

    if (!hasAtLeastOneCompetitor) {
      newErrors.general = 'Please add at least one competitor with retailer and URL';
    }

    if (Object.keys(competitorErrors).length > 0) {
      newErrors.competitors = competitorErrors;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [thaiWatsuduInput, competitorEntries]);

  // Go to review
  const handleGoToReview = useCallback(() => {
    if (validateInputStage()) {
      setStage('review');
    }
  }, [validateInputStage]);

  // Submit comparison with scraping
  const handleConfirmAndCompare = useCallback(async () => {
    setIsSubmitting(true);
    setIsScraping(true);
    setErrors({});
    setScrapeErrors([]);
    setScrapedProducts([]);
    setStage('scraping');

    try {
      const validCompetitors = competitorEntries.filter((e) => e.retailer && e.url.trim());

      // Collect all URLs to scrape
      const urlsToScrape = [
        thaiWatsuduInput.url,
        ...validCompetitors.map((e) => e.url),
      ];

      setScrapeProgress({ current: 0, total: urlsToScrape.length });

      // Call the scrape API
      const scrapeResponse = await apiFetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls: urlsToScrape }),
      });

      if (!scrapeResponse.ok) {
        throw new Error('Failed to scrape URLs');
      }

      const scrapeResult = await scrapeResponse.json();
      setScrapedProducts(scrapeResult.results || []);
      setScrapeErrors(scrapeResult.errors || []);
      setScrapeProgress({ current: scrapeResult.total_scraped, total: urlsToScrape.length });
      setIsScraping(false);

      // Now submit comparison with scraped data
      const response = await apiFetch('/api/comparison/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thaiwatsadu: thaiWatsuduInput,
          competitors: validCompetitors.map((e) => ({ retailer: e.retailer, url: e.url })),
          scraped_data: scrapeResult.results || [],
        }),
      });

      if (!response.ok) throw new Error('Failed to process comparison');

      const result = await response.json();
      setComparisonResult(result);
      setStage('results');
    } catch (err) {
      console.error('Error:', err);
      setErrors({ general: 'Failed to process comparison. Please try again.' });
      setStage('review');
    } finally {
      setIsSubmitting(false);
      setIsScraping(false);
    }
  }, [thaiWatsuduInput, competitorEntries]);

  // Start new comparison
  const handleStartNewComparison = useCallback(() => {
    setStage('input');
    setThaiWatsuduInput({ sku: '', url: '' });
    setCompetitorEntries([{ id: `competitor-${Date.now()}`, retailer: '', url: '' }]);
    setComparisonResult(null);
    setErrors({});
    setScrapedProducts([]);
    setScrapeErrors([]);
    setScrapeProgress({ current: 0, total: 0 });
    setExistingMatches([]);
    setVerifiedRetailers([]);
    setProductFound(null);
  }, []);

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Breadcrumb */}
        <nav className="text-sm text-gray-500">
          <span>Home</span>
          <span className="mx-2">/</span>
          <span className="font-medium text-gray-900">Manual Comparison</span>
        </nav>

        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Manual Comparison</h1>
        </div>

        {/* Stage Indicator */}
        <StageIndicator currentStage={stage} />

        {/* STAGE 1: INPUT */}
        {stage === 'input' && (
          <div className="mx-auto max-w-4xl space-y-8">
            {/* Thai Watsadu Input */}
            <div>
              <div className="mb-4 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-cyan-500 text-white flex items-center justify-center font-bold shadow-md">
                  1
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Thai Watsadu Product</h2>
              </div>
              <p className="mb-4 text-sm text-gray-600">
                Enter the details of the product you want to compare from Thai Watsadu
              </p>

              {/* Thai Watsadu Input Card */}
              <div className="bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-600 rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-200">
                <div className="px-4 py-3 flex items-center gap-2" style={{ backgroundColor: THAI_WATSADU_COLOR }}>
                  <Image
                    src="/logos/thaiwatsadu.svg"
                    alt="Thai Watsadu"
                    width={24}
                    height={24}
                    className="object-contain"
                  />
                  <span className="text-sm font-bold text-white">Thai Watsadu (Source Product)</span>
                </div>

                <div className="p-6 bg-white space-y-4">
                  {/* SKU Input */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="block text-sm font-semibold text-gray-900">
                        SKU <span className="text-red-600">*</span>
                      </label>
                      <Info className="w-4 h-4 text-gray-400" />
                    </div>
                    <div
                      className={`
                        bg-gray-50 rounded-lg px-4 py-3 min-h-[52px] border-2 transition-all duration-200
                        ${errors.thaiWatsadu?.sku
                          ? 'border-red-400 ring-2 ring-red-100'
                          : isSkuValid
                          ? 'border-green-400 ring-2 ring-green-100'
                          : 'border-gray-200 hover:border-red-300 focus-within:border-red-500 focus-within:ring-2 focus-within:ring-red-100'
                        }
                      `}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={thaiWatsuduInput.sku}
                          onChange={(e) => setThaiWatsuduInput((prev) => ({ ...prev, sku: e.target.value }))}
                          placeholder="e.g., TW-12345-ABC"
                          className="flex-1 bg-transparent border-none outline-none text-gray-900 placeholder-gray-400 font-medium"
                        />
                        {isSkuValid && !errors.thaiWatsadu?.sku && (
                          <Check className="w-5 h-5 text-green-600 flex-shrink-0" />
                        )}
                      </div>
                    </div>
                    {errors.thaiWatsadu?.sku ? (
                      <p className="text-xs text-red-600 font-medium">⚠ {errors.thaiWatsadu.sku}</p>
                    ) : (
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
                      <Info className="w-4 h-4 text-gray-400" />
                    </div>
                    <div
                      className={`
                        bg-gray-50 rounded-lg px-4 py-3 min-h-[52px] border-2 transition-all duration-200
                        ${errors.thaiWatsadu?.url
                          ? 'border-red-400 ring-2 ring-red-100'
                          : isUrlValid
                          ? 'border-green-400 ring-2 ring-green-100'
                          : 'border-gray-200 hover:border-red-300 focus-within:border-red-500 focus-within:ring-2 focus-within:ring-red-100'
                        }
                      `}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="url"
                          value={thaiWatsuduInput.url}
                          onChange={(e) => setThaiWatsuduInput((prev) => ({ ...prev, url: e.target.value }))}
                          placeholder="https://www.thaiwatsadu.com/..."
                          className="flex-1 bg-transparent border-none outline-none text-gray-900 placeholder-gray-400 font-medium"
                        />
                        {isUrlValid && !errors.thaiWatsadu?.url && (
                          <Check className="w-5 h-5 text-green-600 flex-shrink-0" />
                        )}
                      </div>
                    </div>
                    {errors.thaiWatsadu?.url ? (
                      <p className="text-xs text-red-600 font-medium">⚠ {errors.thaiWatsadu.url}</p>
                    ) : (
                      <p className="text-xs text-gray-500 flex items-center gap-1">
                        <Info className="w-3 h-3" />
                        Copy and paste the full URL from your browser address bar
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Existing Matches Info */}
            {productFound && existingMatches.length > 0 && (
              <div className="bg-green-50 border-2 border-green-200 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-green-800">This product already has verified matches</h3>
                    <p className="text-sm text-green-700 mt-1">
                      The following retailers are already matched and will be skipped:
                    </p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {existingMatches.map((match) => {
                        const comp = COMPETITORS.find(c => c.retailerId === match.retailer_id);
                        return (
                          <div
                            key={match.retailer_id}
                            className="flex items-center gap-2 bg-white rounded-lg px-3 py-1.5 border border-green-200"
                          >
                            {comp?.logo && (
                              <Image
                                src={comp.logo}
                                alt={comp?.name || match.retailer_name}
                                width={20}
                                height={20}
                                className="object-contain"
                              />
                            )}
                            <span className="text-sm font-medium text-gray-900">{match.retailer_name}</span>
                            {match.price && (
                              <span className="text-sm text-green-600 font-semibold">฿{match.price.toLocaleString()}</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Loading indicator for checking matches */}
            {isCheckingMatches && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-cyan-500"></div>
                Checking existing matches...
              </div>
            )}

            {/* Competitor Inputs */}
            <div>
              <div className="mb-4 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-cyan-500 text-white flex items-center justify-center font-bold shadow-md">
                  2
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Competitor Products</h2>
              </div>
              <p className="mb-4 text-sm text-gray-600">
                Add up to 5 competitor products to compare against
                {verifiedRetailers.length > 0 && (
                  <span className="text-green-600 ml-1">
                    ({verifiedRetailers.length} already matched)
                  </span>
                )}
              </p>
              <div className="space-y-4">
                {competitorEntries.map((entry) => (
                  <CompetitorInputCard
                    key={entry.id}
                    id={entry.id}
                    retailer={entry.retailer}
                    url={entry.url}
                    onRetailerChange={(retailer) => handleCompetitorRetailerChange(entry.id, retailer)}
                    onUrlChange={(url) => handleCompetitorUrlChange(entry.id, url)}
                    onRemove={() => handleRemoveCompetitor(entry.id)}
                    error={errors.competitors?.[entry.id]}
                    usedRetailers={getUsedRetailers()}
                    alreadyMatchedRetailers={verifiedRetailers}
                  />
                ))}

                {/* Add Competitor Button */}
                {competitorEntries.length < 5 ? (
                  <button
                    type="button"
                    onClick={handleAddCompetitor}
                    className="group flex w-full items-center justify-center gap-3 rounded-xl border-2 border-dashed border-cyan-400 bg-gradient-to-r from-cyan-50 to-cyan-100 px-6 py-5 text-cyan-700 transition-all duration-200 hover:border-cyan-500 hover:from-cyan-100 hover:to-cyan-200 hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]"
                  >
                    <div className="rounded-full bg-cyan-500 p-1.5 group-hover:bg-cyan-600 transition-colors shadow-md">
                      <Plus className="h-5 w-5 text-white" />
                    </div>
                    <span className="font-bold text-base">
                      Add Competitor ({competitorEntries.length}/5)
                    </span>
                  </button>
                ) : (
                  <div className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 px-6 py-5 text-gray-400">
                    <span className="font-semibold">Maximum competitors reached (5/5)</span>
                  </div>
                )}
              </div>
            </div>

            {/* Error Message */}
            {errors.general && (
              <div className="rounded-xl border-2 border-red-300 bg-gradient-to-r from-red-50 to-red-100 p-5 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-500 flex items-center justify-center">
                    <span className="text-white text-xl font-bold">!</span>
                  </div>
                  <div>
                    <p className="text-sm font-bold text-red-800">Error</p>
                    <p className="text-sm font-medium text-red-600">{errors.general}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Next Button */}
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleGoToReview}
                className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-10 py-4 font-bold text-white text-lg shadow-lg transition-all hover:from-cyan-600 hover:to-blue-600 hover:shadow-xl hover:scale-105 active:scale-95"
              >
                Next: Review →
              </button>
            </div>
          </div>
        )}

        {/* STAGE 2: REVIEW */}
        {stage === 'review' && (
          <div className="mx-auto max-w-4xl space-y-6">
            {/* Ready to Compare Header */}
            <div className="bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-xl p-5 shadow-lg">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center shadow-md">
                  <Check className="w-6 h-6 text-cyan-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Ready to Compare</h2>
                  <p className="text-cyan-100">
                    1 Thai Watsadu product vs {competitorEntries.filter(e => e.retailer && e.url).length} competitor{competitorEntries.filter(e => e.retailer && e.url).length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            </div>

            {/* Thai Watsadu Card */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 flex items-center gap-3" style={{ backgroundColor: THAI_WATSADU_COLOR }}>
                <Image
                  src="/logos/thaiwatsadu.svg"
                  alt="Thai Watsadu"
                  width={28}
                  height={28}
                  className="object-contain"
                />
                <div>
                  <h3 className="font-bold text-white text-lg">Thai Watsadu</h3>
                  <p className="text-red-100 text-sm">Source Product</p>
                </div>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-[80px_1fr] gap-4">
                  <div className="text-sm text-gray-500 font-medium">SKU</div>
                  <div className="bg-gray-100 px-3 py-1.5 rounded font-mono text-gray-900 inline-block w-fit">
                    {thaiWatsuduInput.sku}
                  </div>
                  <div className="text-sm text-gray-500 font-medium">URL</div>
                  <a
                    href={thaiWatsuduInput.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-600 hover:text-cyan-700 hover:underline flex items-center gap-1 truncate"
                  >
                    <span className="truncate">{thaiWatsuduInput.url}</span>
                    <ExternalLink className="w-4 h-4 flex-shrink-0" />
                  </a>
                </div>
              </div>
            </div>

            {/* Competitor Products Card */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="font-bold text-gray-900 text-lg">
                  Competitor Products ({competitorEntries.filter(e => e.retailer && e.url).length})
                </h3>
                <p className="text-gray-500 text-sm">Comparing against these retailers</p>
              </div>
              <div className="p-6 space-y-4">
                {competitorEntries
                  .filter((e) => e.retailer && e.url.trim())
                  .map((entry, index) => {
                    const comp = COMPETITORS.find(c => c.id === entry.retailer);
                    return (
                      <div
                        key={entry.id}
                        className="border-2 rounded-xl overflow-hidden"
                        style={{ borderColor: `${comp?.color}40` }}
                      >
                        <div
                          className="px-4 py-3 flex items-center gap-3"
                          style={{ backgroundColor: `${comp?.color}10` }}
                        >
                          <div
                            className="w-7 h-7 rounded-full flex items-center justify-center text-white text-sm font-bold"
                            style={{ backgroundColor: comp?.color }}
                          >
                            {index + 1}
                          </div>
                          {comp?.logo && (
                            <Image
                              src={comp.logo}
                              alt={comp.name}
                              width={24}
                              height={24}
                              className="object-contain"
                            />
                          )}
                          <div>
                            <p className="font-bold text-gray-900">{comp?.name}</p>
                            <p className="text-xs text-gray-600">{comp?.nameTh}</p>
                          </div>
                        </div>
                        <div className="px-4 py-3 bg-white">
                          <a
                            href={entry.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-cyan-600 hover:text-cyan-700 hover:underline flex items-center gap-1 text-sm"
                          >
                            <span className="truncate">{entry.url}</span>
                            <ExternalLink className="w-4 h-4 flex-shrink-0" />
                          </a>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between">
              <button
                type="button"
                onClick={() => setStage('input')}
                className="px-6 py-3 border-2 border-gray-300 rounded-xl font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
              >
                ← Edit Inputs
              </button>
              <button
                type="button"
                onClick={handleConfirmAndCompare}
                disabled={isSubmitting}
                className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl font-bold shadow-lg hover:from-cyan-600 hover:to-blue-600 disabled:opacity-50 transition-all"
              >
                {isSubmitting ? 'Processing...' : 'Confirm & Compare'}
              </button>
            </div>

            {errors.general && (
              <div className="rounded-xl border-2 border-red-300 bg-red-50 p-5">
                <p className="text-sm font-medium text-red-600">{errors.general}</p>
              </div>
            )}
          </div>
        )}

        {/* STAGE 3: SCRAPING */}
        {stage === 'scraping' && (
          <div className="mx-auto max-w-2xl space-y-6">
            {/* Scraping Progress Card */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="bg-gradient-to-r from-cyan-500 to-blue-500 px-6 py-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-3">
                  {isScraping && (
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-white border-t-transparent"></div>
                  )}
                  {isScraping ? 'Scraping Product Data...' : 'Scraping Complete'}
                </h2>
                <p className="text-cyan-100 text-sm mt-1">
                  Fetching product information from retailer websites
                </p>
              </div>

              <div className="p-6 space-y-6">
                {/* Progress Bar */}
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Progress</span>
                    <span>{scrapeProgress.current} / {scrapeProgress.total} URLs</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-cyan-500 to-blue-500 h-3 rounded-full transition-all duration-500"
                      style={{
                        width: scrapeProgress.total > 0
                          ? `${(scrapeProgress.current / scrapeProgress.total) * 100}%`
                          : '0%'
                      }}
                    ></div>
                  </div>
                </div>

                {/* URLs Being Scraped */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900">URLs to Scrape:</h3>
                  <div className="space-y-2">
                    {/* Thai Watsadu */}
                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <Image
                        src="/logos/thaiwatsadu.svg"
                        alt="Thai Watsadu"
                        width={24}
                        height={24}
                        className="object-contain"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">Thai Watsadu</p>
                        <p className="text-xs text-gray-500 truncate">{thaiWatsuduInput.url}</p>
                      </div>
                      {scrapedProducts.some(p => p.source_url === thaiWatsuduInput.url || p.url === thaiWatsuduInput.url) ? (
                        <Check className="w-5 h-5 text-green-500" />
                      ) : scrapeErrors.some(e => e.url === thaiWatsuduInput.url) ? (
                        <X className="w-5 h-5 text-red-500" />
                      ) : isScraping ? (
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-cyan-500 border-t-transparent"></div>
                      ) : null}
                    </div>

                    {/* Competitors */}
                    {competitorEntries
                      .filter((e) => e.retailer && e.url.trim())
                      .map((entry) => {
                        const comp = COMPETITORS.find(c => c.id === entry.retailer);
                        const isScraped = scrapedProducts.some(p => p.source_url === entry.url || p.url === entry.url);
                        const hasError = scrapeErrors.some(e => e.url === entry.url);
                        return (
                          <div key={entry.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                            {comp?.logo && (
                              <Image
                                src={comp.logo}
                                alt={comp.name}
                                width={24}
                                height={24}
                                className="object-contain"
                              />
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900">{comp?.name || entry.retailer}</p>
                              <p className="text-xs text-gray-500 truncate">{entry.url}</p>
                            </div>
                            {isScraped ? (
                              <Check className="w-5 h-5 text-green-500" />
                            ) : hasError ? (
                              <X className="w-5 h-5 text-red-500" />
                            ) : isScraping ? (
                              <div className="animate-spin rounded-full h-5 w-5 border-2 border-cyan-500 border-t-transparent"></div>
                            ) : null}
                          </div>
                        );
                      })}
                  </div>
                </div>

                {/* Scraped Results Preview */}
                {scrapedProducts.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-semibold text-gray-900">Scraped Data Preview:</h3>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {scrapedProducts.map((product, index) => (
                        <div key={index} className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                          {product.images && product.images[0] && (
                            <img
                              src={product.images[0]}
                              alt=""
                              className="w-12 h-12 object-contain rounded bg-white"
                            />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 line-clamp-1">{product.name || 'Unknown'}</p>
                            <p className="text-xs text-gray-500">{product.retailer} | SKU: {product.sku || '-'}</p>
                          </div>
                          {product.current_price && (
                            <span className="text-lg font-bold text-green-600">
                              ฿{product.current_price.toLocaleString()}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Errors */}
                {scrapeErrors.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-semibold text-red-600">Errors:</h3>
                    {scrapeErrors.map((error, index) => (
                      <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-700 truncate">{error.url}</p>
                        <p className="text-xs text-red-500">{error.error}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Processing message */}
            {!isScraping && scrapedProducts.length > 0 && (
              <div className="text-center text-gray-600">
                <div className="animate-pulse">Processing comparison...</div>
              </div>
            )}
          </div>
        )}

        {/* STAGE 4: RESULTS */}
        {stage === 'results' && comparisonResult && (
          <div className="mx-auto max-w-6xl space-y-6">
            {/* Apple-style Comparison Table */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  {/* Header Row with Retailer Logos */}
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="px-6 py-6 text-left text-sm font-semibold text-gray-700 w-48 bg-gray-50">
                        Compare
                      </th>
                      {comparisonResult.results?.map((result: any, index: number) => {
                        const comp = index === 0 ? null : COMPETITORS.find(c => c.name === result.retailer || c.id === result.retailer);
                        return (
                          <th key={index} className="px-6 py-6 text-center min-w-[200px]">
                            {index === 0 ? (
                              <Image
                                src="/logos/thaiwatsadu.svg"
                                alt="Thai Watsadu"
                                width={120}
                                height={40}
                                className="object-contain mx-auto"
                              />
                            ) : comp?.logo ? (
                              <Image
                                src={comp.logo}
                                alt={result.retailer}
                                width={120}
                                height={40}
                                className="object-contain mx-auto"
                              />
                            ) : (
                              <span className="font-bold text-gray-900">{result.retailer}</span>
                            )}
                          </th>
                        );
                      })}
                    </tr>
                  </thead>

                  <tbody>
                    {/* Product Image Row */}
                    <tr className="border-b border-gray-200">
                      <td className="px-6 py-6 text-sm font-semibold text-gray-700 bg-gray-50">
                        Compare
                      </td>
                      {comparisonResult.results?.map((result: any, index: number) => (
                        <td key={index} className="px-6 py-6 text-center">
                          {result.image ? (
                            <img
                              src={result.image}
                              alt={result.name || 'Product'}
                              className="w-24 h-24 object-contain mx-auto rounded-lg bg-gray-50"
                            />
                          ) : (
                            <div className="w-24 h-24 mx-auto bg-gray-100 rounded-lg flex items-center justify-center">
                              <span className="text-gray-400 text-xs">No Image</span>
                            </div>
                          )}
                          <p className="mt-2 text-sm font-medium text-gray-900 line-clamp-2">
                            {result.name || 'Product'}
                          </p>
                        </td>
                      ))}
                    </tr>

                    {/* Section: Price Comparison */}
                    <tr className="bg-gray-50">
                      <td colSpan={comparisonResult.results?.length + 1} className="px-6 py-3">
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                          Price Comparison
                        </span>
                      </td>
                    </tr>

                    <tr className="border-b border-gray-200">
                      <td className="px-6 py-4 text-sm font-medium text-gray-700 bg-gray-50">
                        Price
                      </td>
                      {comparisonResult.results?.map((result: any, index: number) => (
                        <td key={index} className="px-6 py-4 text-center">
                          {result.price ? (
                            <span className={`text-xl font-bold ${result.is_lowest ? 'text-green-600' : 'text-gray-900'}`}>
                              ฿{result.price.toLocaleString()}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                          {result.is_lowest && (
                            <div className="mt-1">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                <Check className="w-3 h-3 mr-1" />
                                Lowest
                              </span>
                            </div>
                          )}
                        </td>
                      ))}
                    </tr>

                    {/* Section: Product Information */}
                    <tr className="bg-gray-50">
                      <td colSpan={comparisonResult.results?.length + 1} className="px-6 py-3">
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                          Product Information
                        </span>
                      </td>
                    </tr>

                    <tr className="border-b border-gray-200">
                      <td className="px-6 py-4 text-sm font-medium text-gray-700 bg-gray-50">
                        Product Name
                      </td>
                      {comparisonResult.results?.map((result: any, index: number) => (
                        <td key={index} className="px-6 py-4 text-center">
                          <span className="text-sm text-cyan-600 font-medium">
                            {result.name || '-'}
                          </span>
                        </td>
                      ))}
                    </tr>

                    <tr className="border-b border-gray-200">
                      <td className="px-6 py-4 text-sm font-medium text-gray-700 bg-gray-50">
                        SKU
                      </td>
                      {comparisonResult.results?.map((result: any, index: number) => (
                        <td key={index} className="px-6 py-4 text-center">
                          <span className="text-sm text-gray-900">{result.sku || '-'}</span>
                        </td>
                      ))}
                    </tr>

                    <tr className="border-b border-gray-200">
                      <td className="px-6 py-4 text-sm font-medium text-gray-700 bg-gray-50">
                        Brand
                      </td>
                      {comparisonResult.results?.map((result: any, index: number) => {
                        const baseResult = comparisonResult.results?.[0];
                        const isMatching = index > 0 && result.brand && baseResult?.brand && result.brand === baseResult.brand;
                        return (
                          <td key={index} className="px-6 py-4 text-center">
                            <span className="text-sm text-gray-900">{result.brand || '-'}</span>
                            {isMatching && (
                              <Check className="w-4 h-4 text-green-500 inline-block ml-1" />
                            )}
                          </td>
                        );
                      })}
                    </tr>

                    <tr className="border-b border-gray-200">
                      <td className="px-6 py-4 text-sm font-medium text-gray-700 bg-gray-50">
                        Category
                      </td>
                      {comparisonResult.results?.map((result: any, index: number) => {
                        const baseResult = comparisonResult.results?.[0];
                        const isMatching = index > 0 && result.category && baseResult?.category && result.category === baseResult.category;
                        return (
                          <td key={index} className="px-6 py-4 text-center">
                            <span className="text-sm text-gray-900">{result.category || '-'}</span>
                            {isMatching && (
                              <Check className="w-4 h-4 text-green-500 inline-block ml-1" />
                            )}
                          </td>
                        );
                      })}
                    </tr>

                    {/* Section: Product Links */}
                    <tr className="bg-gray-50">
                      <td colSpan={comparisonResult.results?.length + 1} className="px-6 py-3">
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                          Product Links
                        </span>
                      </td>
                    </tr>

                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-gray-700 bg-gray-50">
                        Product Link
                      </td>
                      {comparisonResult.results?.map((result: any, index: number) => (
                        <td key={index} className="px-6 py-4 text-center">
                          {result.url ? (
                            <a
                              href={result.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-cyan-600 hover:text-cyan-700 hover:underline text-sm font-medium"
                            >
                              View Product
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-center gap-4">
              <Link
                href="/products"
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-8 py-3 font-semibold text-white transition-all hover:from-cyan-600 hover:to-blue-600 hover:shadow-lg"
              >
                <ExternalLink className="h-5 w-5" />
                View in Products
              </Link>
              <button
                type="button"
                onClick={handleStartNewComparison}
                className="flex items-center gap-2 rounded-xl border-2 border-gray-300 bg-white px-8 py-3 font-semibold text-gray-700 transition-colors hover:bg-gray-50"
              >
                <RotateCcw className="h-5 w-5" />
                Start New Comparison
              </button>
            </div>
          </div>
        )}
      </div>

    </MainLayout>
  );
}
