'use client';

import { useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';

export default function PageUnloadTracker() {
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;

    const handleBeforeUnload = () => {
      // Use sendBeacon for reliable tracking when page closes
      // This works even when the page is closing
      const token = localStorage.getItem('auth_token');
      if (token) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        // sendBeacon sends data asynchronously and doesn't block page unload
        navigator.sendBeacon(
          `${apiUrl}/api/auth/page-unload`,
          JSON.stringify({ timestamp: new Date().toISOString() })
        );
      }
    };

    // Track when user closes tab/browser or navigates away
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Track when page is hidden (mobile browsers)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        handleBeforeUnload();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [user]);

  return null;
}
