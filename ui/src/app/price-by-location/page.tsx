'use client';

import { MainLayout } from '@/components/layout/MainLayout';

// TODO: Price by Location feature - Database not set up in UAT yet
// Temporarily disabled to prevent build errors
export default function PriceByLocationPage() {
  return (
    <MainLayout>
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Price by Location
          </h1>
          <p className="text-gray-600">
            This feature is currently under development.
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Database setup required before enabling this page.
          </p>
        </div>
      </div>
    </MainLayout>
  );
}
