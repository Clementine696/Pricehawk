'use client';

import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Package, TrendingDown, Store, GitCompare } from 'lucide-react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';

interface DashboardStats {
  total_products: number;
  total_retailers: number;
  total_matches: number;
  pending_reviews: number;
}

interface Retailer {
  retailer_id: string;
  name: string;
  product_count: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_products: 0,
    total_retailers: 0,
    total_matches: 0,
    pending_reviews: 0,
  });
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, retailersRes] = await Promise.all([
        apiFetch('/api/dashboard/stats'),
        apiFetch('/api/retailers'),
      ]);

      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }

      if (retailersRes.ok) {
        const data = await retailersRes.json();
        setRetailers(data);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Products',
      value: stats.total_products,
      icon: Package,
      color: 'bg-blue-500',
      href: '/products',
    },
    {
      title: 'Retailers',
      value: stats.total_retailers,
      icon: Store,
      color: 'bg-green-500',
      href: '/products',
    },
    {
      title: 'Product Matches',
      value: stats.total_matches,
      icon: GitCompare,
      color: 'bg-purple-500',
      href: '/comparison',
    },
    {
      title: 'Pending Reviews',
      value: stats.pending_reviews,
      icon: TrendingDown,
      color: 'bg-orange-500',
      href: '/comparison',
    },
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome to PriceHawk price monitoring system</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statCards.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.title}
                href={card.href}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center">
                  <div className={`${card.color} p-3 rounded-lg`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-500">{card.title}</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {isLoading ? '-' : card.value.toLocaleString()}
                    </p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/products"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Package className="w-8 h-8 text-cyan-500" />
              <div>
                <p className="font-medium text-gray-900">View Products</p>
                <p className="text-sm text-gray-500">Browse all tracked products</p>
              </div>
            </Link>
            <Link
              href="/comparison"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <GitCompare className="w-8 h-8 text-purple-500" />
              <div>
                <p className="font-medium text-gray-900">Review Matches</p>
                <p className="text-sm text-gray-500">Verify product matches</p>
              </div>
            </Link>
            <div className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg bg-gray-50">
              <TrendingDown className="w-8 h-8 text-green-500" />
              <div>
                <p className="font-medium text-gray-900">Price Alerts</p>
                <p className="text-sm text-gray-500">Coming soon</p>
              </div>
            </div>
          </div>
        </div>

        {/* Retailers Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Retailers Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {isLoading ? (
              <div className="col-span-full text-center py-8 text-gray-500">Loading retailers...</div>
            ) : retailers.length === 0 ? (
              <div className="col-span-full text-center py-8 text-gray-500">No retailers found</div>
            ) : (
              retailers.map((retailer) => (
                <div
                  key={retailer.retailer_id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-cyan-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-900">{retailer.name}</h3>
                    <Store className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Products</span>
                    <span className="text-lg font-semibold text-cyan-600">
                      {retailer.product_count.toLocaleString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
