/**
 * API base URL - uses environment variable in production, empty string for local development
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Token storage key
const TOKEN_KEY = 'auth_token';

// Debug: Log the API_BASE_URL (will show in browser console)
if (typeof window !== 'undefined') {
  console.log('[api.ts] API_BASE_URL:', API_BASE_URL || '(empty - using same origin)');
}

/**
 * Get stored auth token from localStorage
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store auth token in localStorage
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Remove auth token from localStorage
 */
export function removeAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
}

interface ApiFetchOptions extends RequestInit {
  skipAuthRedirect?: boolean;
}

/**
 * API utility that handles 401 Unauthorized errors by redirecting to login
 * @param skipAuthRedirect - Set to true to skip automatic redirect on 401 (useful for auth checks)
 */
export async function apiFetch(url: string, options: ApiFetchOptions = {}): Promise<Response> {
  const { skipAuthRedirect, ...fetchOptions } = options;

  // Prepend API base URL for production deployment
  const fullUrl = url.startsWith('/api') ? `${API_BASE_URL}${url}` : url;

  // Get auth token and add to headers
  const token = getAuthToken();
  const headers = new Headers(fetchOptions.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Debug: Log the actual URL being called
  console.log('[api.ts] Fetching:', fullUrl);

  const response = await fetch(fullUrl, {
    ...fetchOptions,
    headers,
    credentials: 'include',  // Keep for backward compatibility with cookies
  });

  // Redirect to login on 401 Unauthorized (unless skipAuthRedirect is set)
  if (response.status === 401 && !skipAuthRedirect) {
    // Clear token on auth failure
    removeAuthToken();
    // Only redirect if we're in the browser and not already on login page
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  return response;
}
