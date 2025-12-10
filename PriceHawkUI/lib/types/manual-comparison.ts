/**
 * Manual Comparison Types
 * Types for the manual SKU/URL comparison feature
 */

// Competitor retailer type (excludes Thai Watsadu as source)
export type CompetitorRetailer =
  | 'HOMEPRO'
  | 'MEGA_HOME'
  | 'BOONTHAVORN'
  | 'GLOBAL_HOUSE'
  | 'DOHOME';

// Competitor info with display properties
export interface CompetitorInfo {
  id: CompetitorRetailer;
  name: string;
  nameTh: string;
  domain: string;
  logo?: string;
  color: string; // Brand color for UI display
}

// Input form state (legacy)
export interface ManualComparisonInput {
  thaiwatsuduInput: string; // SKU or URL
  inputType: 'sku' | 'url';
  selectedCompetitors: CompetitorRetailer[];
  competitorUrls: Partial<Record<CompetitorRetailer, string>>;
}

// New Manual Comparison Journey - Side A (Thai Watsadu input)
export interface ThaiWatsuduInput {
  sku: string; // Required
  url: string; // Required
}

// New Manual Comparison Journey - Competitor URL entry
export interface CompetitorUrlEntry {
  id: string; // Unique ID for the entry
  retailer: CompetitorRetailer;
  urls: string[]; // Can have multiple URLs per competitor
}

// New Manual Comparison Journey - Full input state
export interface ManualComparisonInputV2 {
  thaiWatsadu: ThaiWatsuduInput;
  competitors: CompetitorUrlEntry[];
}

// Source product fetched from Thaiwatsadu
export interface SourceProduct {
  sku: string;
  name: string;
  nameTh?: string;
  price: number;
  imageUrl: string;
  productUrl: string;
  category?: string;
  brand?: string;
}

// Match status for competitor results
export type MatchStatus = 'match' | 'not_match' | 'pending' | 'error';

// Individual URL comparison result
export interface UrlComparisonResult {
  url: string;
  status: MatchStatus;
  confidence: number; // 0-100
  matchedProduct?: {
    sku: string;
    name: string;
    price: number;
    imageUrl: string;
    productUrl: string;
  };
  errorMessage?: string;
}

// Match result for each competitor (updated with multiple URL support)
export interface CompetitorMatchResult {
  competitor: CompetitorRetailer;
  status: MatchStatus;
  confidence: number; // 0-100
  matchedProduct?: {
    sku: string;
    name: string;
    price: number;
    imageUrl: string;
    productUrl: string;
  };
  userVerified?: boolean;
  errorMessage?: string;
  // New fields for multi-URL comparison
  urlResults?: UrlComparisonResult[];
  matchCount?: number;
  notMatchCount?: number;
}

// API request payload (legacy)
export interface ManualComparisonRequest {
  sourceProduct: SourceProduct;
  competitors: CompetitorRetailer[];
  competitorUrls?: Partial<Record<CompetitorRetailer, string>>;
}

// New API request payload for V2 flow
export interface ManualComparisonRequestV2 {
  thaiWatsadu: ThaiWatsuduInput;
  competitors: CompetitorUrlEntry[];
}

// API response
export interface ManualComparisonResponse {
  id: string;
  sourceProduct: SourceProduct;
  results: CompetitorMatchResult[];
  createdAt: string;
}

// Form state for the comparison page
export interface ComparisonFormState {
  isLoading: boolean;
  isFetchingSource: boolean;
  sourceProduct: SourceProduct | null;
  results: CompetitorMatchResult[];
  error: string | null;
}

// User action on a match result
export type MatchAction = 'confirm' | 'reject' | 'retry';

// Batch action request
export interface BatchMatchActionRequest {
  comparisonId: string;
  action: 'confirm_all' | 'retry_failed';
}

// Validation result for user confirmation
export interface ValidationResult {
  competitor: CompetitorRetailer;
  urlMatchResults: {
    url: string;
    status: 'match' | 'not_match';
    confidence: number;
  }[];
  overallVerified?: boolean;
}

// Apple-style comparison table types
export interface ComparisonTableProduct {
  sku: string;
  name: string;
  price: number;
  discountPercentage?: number;
  unitPrice?: number;
  imageUrl?: string;
  productUrl: string;
  brand?: string;
  category?: string;
  stockStatus?: string;
  retailer: 'THAI_WATSADU' | CompetitorRetailer | string;
  retailerLogo?: string;
}

export interface ComparisonTableData {
  thaiWatsadu: ComparisonTableProduct;
  competitors: ComparisonTableProduct[];
}
