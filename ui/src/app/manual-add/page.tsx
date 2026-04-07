'use client';

import { useState, useCallback, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Plus, RotateCcw, Check, X, ExternalLink, Info } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';
import Image from 'next/image';
import { apiFetch } from '@/lib/api';

type ComparisonStage = 'input' | 'review' | 'scraping' | 'results';

const MAKRO_COLOR = '#0066CC';
const CFW_COLOR = '#00875A';

// Stage Indicator
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
              <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300
                  ${isActive ? 'bg-cyan-500 text-white shadow-lg scale-110 ring-2 ring-cyan-400 ring-offset-2'
                    : isCompleted ? 'bg-cyan-500 text-white'
                    : 'bg-gray-200 text-gray-400'}`}>
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

function ManualAddContent() {
  const searchParams = useSearchParams();

  const [stage, setStage] = useState<ComparisonStage>('input');
  const [cfwSku, setCfwSku] = useState('');
  const [makroUrl, setMakroUrl] = useState('');

  // CFW product info (fetched when SKU entered)
  const [cfwProduct, setCfwProduct] = useState<any>(null);
  const [existingMatches, setExistingMatches] = useState<any[]>([]);
  const [isCheckingProduct, setIsCheckingProduct] = useState(false);

  // Scraping state
  const [isScraping, setIsScraping] = useState(false);
  const [scrapedMakro, setScrapedMakro] = useState<any>(null);
  const [scrapeError, setScrapeError] = useState<string | null>(null);

  // Result
  const [comparisonResult, setComparisonResult] = useState<any>(null);

  // Errors
  const [errors, setErrors] = useState<{ sku?: string; url?: string; general?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Pre-fill from query params (from product detail page)
  useEffect(() => {
    const skuParam = searchParams.get('sku');
    if (skuParam) setCfwSku(skuParam);
  }, [searchParams]);

  // Fetch CFW product when SKU changes
  useEffect(() => {
    if (cfwSku.trim().length < 3) {
      setCfwProduct(null);
      setExistingMatches([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsCheckingProduct(true);
      try {
        const res = await apiFetch(`/api/products/sku/${encodeURIComponent(cfwSku.trim())}/matches`);
        if (res.ok) {
          const data = await res.json();
          setCfwProduct(data.found ? data.product : null);
          setExistingMatches(data.matches || []);
        }
      } catch {
        // ignore
      } finally {
        setIsCheckingProduct(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [cfwSku]);

  const validateInput = useCallback(() => {
    const newErrors: typeof errors = {};
    if (!cfwSku.trim()) newErrors.sku = 'CFW SKU is required';
    else if (!cfwProduct) newErrors.sku = 'CFW product not found for this SKU';
    if (!makroUrl.trim()) newErrors.url = 'Makro URL is required';
    else if (!makroUrl.startsWith('http')) newErrors.url = 'URL must start with http:// or https://';
    else if (!makroUrl.includes('makro.pro')) newErrors.url = 'URL must be from makro.pro';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [cfwSku, cfwProduct, makroUrl]);

  const handleGoToReview = useCallback(() => {
    if (validateInput()) setStage('review');
  }, [validateInput]);

  const handleConfirmAndCompare = useCallback(async () => {
    setIsSubmitting(true);
    setIsScraping(true);
    setScrapeError(null);
    setScrapedMakro(null);
    setStage('scraping');

    try {
      // Step 1: Scrape Makro URL
      const scrapeRes = await apiFetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls: [makroUrl] }),
        timeout: 180000,
      });

      if (!scrapeRes.ok) throw new Error('Scrape request failed');
      const scrapeData = await scrapeRes.json();

      const scraped = scrapeData.results?.[0] || null;
      setScrapedMakro(scraped);
      setIsScraping(false);

      if (!scraped || !scraped.name || !scraped.current_price) {
        setScrapeError('Could not extract product data from this Makro URL. Please check the URL is a valid product page.');
        setStage('review');
        setIsSubmitting(false);
        return;
      }

      // Step 2: Save match to DB
      const saveRes = await apiFetch('/api/comparison/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cfw_sku: cfwSku.trim(),
          makro_url: makroUrl.trim(),
          scraped_data: scraped,
        }),
        timeout: 60000,
      });

      if (!saveRes.ok) {
        const err = await saveRes.json().catch(() => ({}));
        if (saveRes.status === 409) {
          setScrapeError(err.detail || 'This product already has a verified match.');
          setStage('input');
          setIsSubmitting(false);
          return;
        }
        throw new Error(err.detail || 'Failed to save match');
      }

      const result = await saveRes.json();
      setComparisonResult(result);
      setStage('results');
    } catch (err: any) {
      setScrapeError(err.message || 'Failed to process comparison. Please try again.');
      setStage('review');
    } finally {
      setIsSubmitting(false);
      setIsScraping(false);
    }
  }, [cfwSku, makroUrl]);

  const handleStartNew = useCallback(() => {
    setStage('input');
    setCfwSku('');
    setMakroUrl('');
    setCfwProduct(null);
    setExistingMatches([]);
    setScrapedMakro(null);
    setScrapeError(null);
    setComparisonResult(null);
    setErrors({});
  }, []);

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Manual Add Match</h1>
          <p className="text-gray-500 mt-1">Find a CFW product and link it to a Makro product</p>
        </div>

        <StageIndicator currentStage={stage} />

        {/* STAGE 1: INPUT */}
        {stage === 'input' && (
          <div className="mx-auto max-w-2xl space-y-6">

            {/* CFW SKU */}
            <div className="bg-white rounded-xl shadow overflow-hidden">
              <div className="px-5 py-3 flex items-center gap-2" style={{ backgroundColor: CFW_COLOR }}>
                <span className="text-sm font-bold text-white">CFW — Central Food Wholesale</span>
              </div>
              <div className="p-5 space-y-3">
                <label className="block text-sm font-semibold text-gray-900">
                  CFW SKU <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={cfwSku}
                  onChange={e => setCfwSku(e.target.value)}
                  placeholder="e.g. 10000034"
                  className={`w-full px-4 py-2.5 border-2 rounded-lg outline-none transition-all
                    ${errors.sku ? 'border-red-400' : cfwProduct ? 'border-green-400' : 'border-gray-200 focus:border-cyan-500'}`}
                />
                {isCheckingProduct && (
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <span className="animate-spin inline-block w-3 h-3 border border-gray-400 border-t-transparent rounded-full" />
                    Looking up product...
                  </p>
                )}
                {cfwProduct && !errors.sku && (
                  <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
                    <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-green-800">{cfwProduct.name}</p>
                      {cfwProduct.price && (
                        <p className="text-xs text-green-600">฿{cfwProduct.price.toLocaleString()}</p>
                      )}
                    </div>
                  </div>
                )}
                {errors.sku && <p className="text-xs text-red-600">⚠ {errors.sku}</p>}

                {/* Existing verified matches */}
                {existingMatches.length > 0 && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-xs font-semibold text-blue-700 mb-2">Already has verified Makro match:</p>
                    {existingMatches.map((m, i) => (
                      <div key={i} className="text-xs text-blue-600">
                        {m.name} {m.price ? `— ฿${m.price.toLocaleString()}` : ''}
                      </div>
                    ))}
                    <p className="text-xs text-blue-500 mt-1">You can still add another match candidate.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Makro URL */}
            <div className="bg-white rounded-xl shadow overflow-hidden">
              <div className="px-5 py-3 flex items-center gap-2" style={{ backgroundColor: MAKRO_COLOR }}>
                <span className="text-sm font-bold text-white">Makro — makro.pro</span>
              </div>
              <div className="p-5 space-y-3">
                <label className="block text-sm font-semibold text-gray-900">
                  Product URL <span className="text-red-500">*</span>
                </label>
                <input
                  type="url"
                  value={makroUrl}
                  onChange={e => setMakroUrl(e.target.value)}
                  placeholder="https://www.makro.pro/product/..."
                  className={`w-full px-4 py-2.5 border-2 rounded-lg outline-none transition-all
                    ${errors.url ? 'border-red-400' : makroUrl.includes('makro.pro') && makroUrl.startsWith('http') ? 'border-green-400' : 'border-gray-200 focus:border-cyan-500'}`}
                />
                {errors.url && <p className="text-xs text-red-600">⚠ {errors.url}</p>}
                {!errors.url && (
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    Paste the full makro.pro product URL
                  </p>
                )}
              </div>
            </div>

            {(errors.general || scrapeError) && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{errors.general || scrapeError}</p>
              </div>
            )}

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => { setScrapeError(null); handleGoToReview(); }}
                className="px-8 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-bold shadow transition-all"
              >
                Next: Review →
              </button>
            </div>
          </div>
        )}

        {/* STAGE 2: REVIEW */}
        {stage === 'review' && (
          <div className="mx-auto max-w-2xl space-y-5">
            <div className="bg-cyan-500 rounded-xl p-5">
              <h2 className="text-xl font-bold text-white">Ready to Compare</h2>
              <p className="text-cyan-100 text-sm mt-1">CFW vs Makro — confirm details before scraping</p>
            </div>

            {/* CFW product card */}
            <div className="bg-white rounded-xl shadow overflow-hidden">
              <div className="px-5 py-3" style={{ backgroundColor: CFW_COLOR }}>
                <span className="text-sm font-bold text-white">CFW Product</span>
              </div>
              <div className="p-5 space-y-2">
                <div className="flex gap-3">
                  <span className="text-sm text-gray-500 w-16 flex-shrink-0">SKU</span>
                  <span className="font-mono text-sm text-gray-900 bg-gray-100 px-2 py-0.5 rounded">{cfwSku}</span>
                </div>
                {cfwProduct && (
                  <>
                    <div className="flex gap-3">
                      <span className="text-sm text-gray-500 w-16 flex-shrink-0">Name</span>
                      <span className="text-sm text-gray-900">{cfwProduct.name}</span>
                    </div>
                    {cfwProduct.price && (
                      <div className="flex gap-3">
                        <span className="text-sm text-gray-500 w-16 flex-shrink-0">Price</span>
                        <span className="text-sm font-bold text-gray-900">฿{cfwProduct.price.toLocaleString()}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Makro URL card */}
            <div className="bg-white rounded-xl shadow overflow-hidden">
              <div className="px-5 py-3" style={{ backgroundColor: MAKRO_COLOR }}>
                <span className="text-sm font-bold text-white">Makro URL to Scrape</span>
              </div>
              <div className="p-5">
                <a
                  href={makroUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyan-600 hover:underline text-sm flex items-center gap-1"
                >
                  <span className="truncate">{makroUrl}</span>
                  <ExternalLink className="w-4 h-4 flex-shrink-0" />
                </a>
              </div>
            </div>

            {scrapeError && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{scrapeError}</p>
              </div>
            )}

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => { setScrapeError(null); setStage('input'); }}>
                ← Edit Inputs
              </Button>
              <button
                type="button"
                onClick={handleConfirmAndCompare}
                disabled={isSubmitting}
                className="px-8 py-3 bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 text-white rounded-xl font-bold shadow transition-all"
              >
                {isSubmitting ? 'Processing...' : 'Confirm & Scrape'}
              </button>
            </div>
          </div>
        )}

        {/* STAGE 3: SCRAPING */}
        {stage === 'scraping' && (
          <div className="mx-auto max-w-xl space-y-5">
            <div className="bg-white rounded-xl shadow p-8 text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-cyan-50 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Scraping Makro...</h2>
              <p className="text-gray-500 text-sm">Fetching product data from makro.pro</p>
              <div className="p-3 bg-gray-50 rounded-lg text-left">
                <p className="text-xs text-gray-500 mb-1 font-medium">Makro URL</p>
                <p className="text-xs text-gray-700 break-all">{makroUrl}</p>
              </div>
            </div>
          </div>
        )}

        {/* STAGE 4: RESULTS */}
        {stage === 'results' && comparisonResult && (
          <div className="mx-auto max-w-2xl space-y-5">
            <div className="bg-white rounded-xl shadow overflow-hidden">
              <div className="px-5 py-4 bg-emerald-500">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Check className="w-5 h-5" />
                  Match Created
                </h2>
                <p className="text-emerald-100 text-sm mt-1">
                  Go to the product detail page to verify this match
                </p>
              </div>

              <div className="p-5 grid grid-cols-2 gap-4">
                {/* CFW */}
                <div className="rounded-lg border-2 overflow-hidden" style={{ borderColor: CFW_COLOR + '40' }}>
                  <div className="px-3 py-2 text-xs font-bold text-white" style={{ backgroundColor: CFW_COLOR }}>
                    CFW
                  </div>
                  <div className="p-3 space-y-1.5">
                    <p className="text-sm font-medium text-gray-900 line-clamp-2">{comparisonResult.cfw_product?.name}</p>
                    <p className="text-lg font-bold text-gray-900">
                      {comparisonResult.cfw_product?.price ? `฿${comparisonResult.cfw_product.price.toLocaleString()}` : '—'}
                    </p>
                  </div>
                </div>

                {/* Makro */}
                <div className="rounded-lg border-2 overflow-hidden" style={{ borderColor: MAKRO_COLOR + '40' }}>
                  <div className="px-3 py-2 text-xs font-bold text-white" style={{ backgroundColor: MAKRO_COLOR }}>
                    Makro
                  </div>
                  <div className="p-3 space-y-1.5">
                    {comparisonResult.makro_product?.image && (
                      <img
                        src={comparisonResult.makro_product.image}
                        alt=""
                        className="w-16 h-16 object-contain bg-gray-50 rounded mb-2"
                        referrerPolicy="no-referrer"
                      />
                    )}
                    <p className="text-sm font-medium text-gray-900 line-clamp-2">{comparisonResult.makro_product?.name}</p>
                    <p className="text-xs text-gray-500">SKU: {comparisonResult.makro_product?.sku || '—'}</p>
                    <p className="text-lg font-bold text-gray-900">
                      {comparisonResult.makro_product?.price ? `฿${comparisonResult.makro_product.price.toLocaleString()}` : '—'}
                    </p>
                    {comparisonResult.makro_product?.url && (
                      <a
                        href={comparisonResult.makro_product.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-cyan-600 hover:underline flex items-center gap-1"
                      >
                        View on Makro <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-center gap-4">
              <Link
                href={comparisonResult.cfw_product ? `/products/${cfwSku}` : '/products'}
                className="flex items-center gap-2 px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-semibold shadow transition-all"
              >
                <ExternalLink className="w-4 h-4" />
                View Product & Verify
              </Link>
              <Button variant="outline" onClick={handleStartNew} icon={<RotateCcw className="w-4 h-4" />}>
                New Comparison
              </Button>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}

export default function ManualAddPage() {
  return (
    <Suspense fallback={
      <MainLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
        </div>
      </MainLayout>
    }>
      <ManualAddContent />
    </Suspense>
  );
}
