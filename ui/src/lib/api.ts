/**
 * API base URL - uses environment variable in production, empty string for local development
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Debug: Log the API_BASE_URL (will show in browser console)
if (typeof window !== 'undefined') {
  console.log('[api.ts] API_BASE_URL:', API_BASE_URL || '(empty - using same origin)');
}

/**
 * API utility that handles 401 Unauthorized errors by redirecting to login
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  // Prepend API base URL for production deployment
  const fullUrl = url.startsWith('/api') ? `${API_BASE_URL}${url}` : url;

  // Debug: Log the actual URL being called
  console.log('[api.ts] Fetching:', fullUrl);

  const response = await fetch(fullUrl, {
    ...options,
    credentials: 'include',
  });

  // Redirect to login on 401 Unauthorized
  if (response.status === 401) {
    // Only redirect if we're in the browser
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  return response;
}
