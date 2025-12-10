/**
 * API base URL - uses environment variable in production, empty string for local development
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * API utility that handles 401 Unauthorized errors by redirecting to login
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  // Prepend API base URL for production deployment
  const fullUrl = url.startsWith('/api') ? `${API_BASE_URL}${url}` : url;

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
