/**
 * API base URL - uses environment variable in production, empty string for local development
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Debug: Log the API_BASE_URL (will show in browser console)
if (typeof window !== 'undefined') {
  console.log('[api.ts] API_BASE_URL:', API_BASE_URL || '(empty - using same origin)');
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

  // Debug: Log the actual URL being called
  console.log('[api.ts] Fetching:', fullUrl);

  const response = await fetch(fullUrl, {
    ...fetchOptions,
    credentials: 'include',
  });

  // Redirect to login on 401 Unauthorized (unless skipAuthRedirect is set)
  if (response.status === 401 && !skipAuthRedirect) {
    // Only redirect if we're in the browser and not already on login page
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  return response;
}
