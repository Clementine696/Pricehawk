'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Package, GitCompare, Settings, LogOut, PlusCircle, Bell, MapPin } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

// Custom ListChecks icon component
const ListChecks: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="m3 17 2 2 4-4"></path>
    <path d="m3 7 2 2 4-4"></path>
    <path d="M13 6h8"></path>
    <path d="M13 12h8"></path>
    <path d="M13 18h8"></path>
  </svg>
);

const menuItems = [
  {
    href: '/dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
  },
  {
    href: '/products',
    label: 'Products',
    icon: Package,
  },
  {
    href: '/manual-add',
    label: 'Manual Add',
    icon: PlusCircle,
  },
  {
    href: '/watchlist-sku',
    label: 'Watchlist',
    icon: ListChecks,
  },
  {
    href: '/alert',
    label: 'Price Alerts',
    icon: Bell,
  },
  {
    href: '/price-by-location',
    label: 'Price by Location',
    icon: MapPin,
  },
  // {
  //   href: '/comparison',
  //   label: 'Comparison',
  //   icon: GitCompare,
  // },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="w-56 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="px-4 flex items-center justify-center h-16">
        <Image
          src="/logos/pricehawk_logo.svg"
          alt="PriceHawk"
          width={140}
          height={40}
          className="object-contain"
          priority
        />
      </div>

      <div className="px-4 py-1 border-b border-gray-200"></div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const isActive = pathname?.startsWith(item.href);
            const Icon = item.icon;

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-cyan-500 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">{user?.username}</span>
          <button
            onClick={logout}
            className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
