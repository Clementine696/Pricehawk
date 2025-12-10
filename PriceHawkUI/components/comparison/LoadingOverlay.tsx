'use client';

import { Loader2 } from 'lucide-react';

interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message = 'Processing comparison...' }: LoadingOverlayProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        <div className="flex flex-col items-center space-y-4">
          {/* Spinner */}
          <Loader2 className="w-12 h-12 text-cyan-500 animate-spin" />

          {/* Message */}
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Please wait
            </h3>
            <p className="text-sm text-gray-600">{message}</p>
          </div>

          {/* Skeleton Loaders */}
          <div className="w-full space-y-3 pt-4">
            <div className="h-4 bg-gray-200 rounded animate-shimmer" />
            <div className="h-4 bg-gray-200 rounded animate-shimmer w-3/4" />
            <div className="h-4 bg-gray-200 rounded animate-shimmer w-5/6" />
          </div>
        </div>
      </div>
    </div>
  );
}
