// Google Analytics utility functions
// Tracks page views, events, and user engagement

declare global {
  interface Window {
    gtag: (...args: any[]) => void;
    dataLayer: any[];
  }
}

export const GA_TRACKING_ID = 'G-Y4YCTMYX01';

// Track page view
export const pageview = (url: string) => {
  if (typeof window.gtag !== 'undefined') {
    window.gtag('config', GA_TRACKING_ID, {
      page_path: url,
    });
  }
};

// Track custom events
export const event = ({ action, category, label, value }: {
  action: string;
  category: string;
  label?: string;
  value?: number;
}) => {
  if (typeof window.gtag !== 'undefined') {
    window.gtag('event', action, {
      event_category: category,
      event_label: label,
      value: value,
    });
  }
};

// Set user ID for logged-in users (for cross-session tracking)
export const setUserId = (userId: string | null) => {
  if (typeof window.gtag !== 'undefined') {
    window.gtag('config', GA_TRACKING_ID, {
      user_id: userId,
    });
  }
};

// Track user login
export const trackLogin = (username: string) => {
  event({
    action: 'login',
    category: 'User',
    label: username,
  });
  setUserId(username);
};

// Track user logout
export const trackLogout = () => {
  event({
    action: 'logout',
    category: 'User',
  });
  setUserId(null);
};

// Track product view
export const trackProductView = (productId: number, productName: string, retailer: string) => {
  event({
    action: 'view_product',
    category: 'Products',
    label: `${retailer} - ${productName}`,
    value: productId,
  });
};

// Track export action
export const trackExport = (exportType: string, itemCount?: number) => {
  event({
    action: 'export',
    category: 'Data',
    label: exportType,
    value: itemCount,
  });
};

// Track match verification
export const trackMatchVerification = (matchId: number, isSame: boolean) => {
  event({
    action: 'verify_match',
    category: 'Matching',
    label: isSame ? 'confirmed' : 'rejected',
    value: matchId,
  });
};

// Track manual comparison
export const trackManualComparison = (retailerCount: number) => {
  event({
    action: 'manual_comparison',
    category: 'Scraping',
    label: 'initiated',
    value: retailerCount,
  });
};

// Track search
export const trackSearch = (searchTerm: string) => {
  event({
    action: 'search',
    category: 'Products',
    label: searchTerm,
  });
};

// Track filter usage
export const trackFilter = (filterType: string, filterValue: string) => {
  event({
    action: 'filter',
    category: 'Products',
    label: `${filterType}: ${filterValue}`,
  });
};
