'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/layout/MainLayout';
import { apiFetch } from '@/lib/api';
import { MapPin, ListChecks, CheckCircle2, Loader2, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface Watchlist {
  id: number;
  name: string;
  description: string | null;
  product_count: number;
}

interface Location {
  id: number;
  name: string;
  branch_code: string;
  region: string | null;
}

export default function PblSettingsPage() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedWatchlists, setSelectedWatchlists] = useState<number[]>([]);
  const [selectedLocations, setSelectedLocations] = useState<number[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const [searchWatchlist, setSearchWatchlist] = useState('');
  const [searchLocation, setSearchLocation] = useState('');
  const [watchlistFilter, setWatchlistFilter] = useState<'all' | 'selected'>('all');
  const [locationFilter, setLocationFilter] = useState<'all' | 'selected'>('all');

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setIsLoading(true);
    try {
      const [wRes, lRes, sRes] = await Promise.all([
        apiFetch('/api/watchlists'),
        apiFetch('/api/pbl/locations'),
        apiFetch('/api/pbl/settings'),
      ]);
      if (wRes.ok) setWatchlists((await wRes.json()).watchlists);
      if (lRes.ok) setLocations((await lRes.json()).locations);
      if (sRes.ok) {
        const s = await sRes.json();
        setSelectedWatchlists(s.watchlist_ids);
        setSelectedLocations(s.location_ids);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    setSuccess('');
    try {
      const res = await apiFetch('/api/pbl/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ watchlist_ids: selectedWatchlists, location_ids: selectedLocations }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Failed to save');
      }
      setSuccess('Settings saved!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setIsSaving(false);
    }
  };

  const toggleWatchlist = (id: number) =>
    setSelectedWatchlists(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const toggleLocation = (id: number) =>
    setSelectedLocations(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const filteredWatchlists = watchlists.filter(w => {
    const matchSearch = !searchWatchlist || w.name.toLowerCase().includes(searchWatchlist.toLowerCase());
    const matchFilter = watchlistFilter === 'all' || selectedWatchlists.includes(w.id);
    return matchSearch && matchFilter;
  });

  const filteredLocations = locations.filter(l => {
    const matchSearch = !searchLocation ||
      l.name.toLowerCase().includes(searchLocation.toLowerCase()) ||
      l.branch_code.includes(searchLocation);
    const matchFilter = locationFilter === 'all' || selectedLocations.includes(l.id);
    return matchSearch && matchFilter;
  });

  const allWatchlistsSelected = filteredWatchlists.length > 0 && filteredWatchlists.every(w => selectedWatchlists.includes(w.id));
  const allLocationsSelected = filteredLocations.length > 0 && filteredLocations.every(l => selectedLocations.includes(l.id));

  const toggleAllWatchlists = () => {
    if (allWatchlistsSelected) {
      setSelectedWatchlists(prev => prev.filter(id => !filteredWatchlists.some(w => w.id === id)));
    } else {
      setSelectedWatchlists(prev => Array.from(new Set([...prev, ...filteredWatchlists.map(w => w.id)])));
    }
  };

  const toggleAllLocations = () => {
    if (allLocationsSelected) {
      setSelectedLocations(prev => prev.filter(id => !filteredLocations.some(l => l.id === id)));
    } else {
      setSelectedLocations(prev => Array.from(new Set([...prev, ...filteredLocations.map(l => l.id)])));
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center py-32">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Back */}
        <Link href="/price-by-location-makro" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 text-sm">
          <ArrowLeft className="w-4 h-4" />
          Back to Price by Location
        </Link>

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Price by Location — Settings</h1>
            <p className="text-gray-500 mt-1">Select watchlists and Makro postal zones to monitor</p>
          </div>
          <Button variant="primary" onClick={handleSave} loading={isSaving}>
            Save Settings
          </Button>
        </div>

        {/* Messages */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}
        {success && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />{success}
          </div>
        )}

        {/* Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow p-5 flex items-center gap-4">
            <div className="bg-cyan-500 p-3 rounded-lg">
              <ListChecks className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Selected Watchlists</p>
              <p className="text-2xl font-bold text-gray-900">{selectedWatchlists.length}</p>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-5 flex items-center gap-4">
            <div className="bg-blue-500 p-3 rounded-lg">
              <MapPin className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Selected Locations</p>
              <p className="text-2xl font-bold text-gray-900">{selectedLocations.length}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Watchlists */}
          <section className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <ListChecks className="w-5 h-5 text-cyan-600" />
                Watchlists
              </h2>
              <button onClick={toggleAllWatchlists} className="text-sm text-cyan-600 hover:text-cyan-700 font-medium">
                {allWatchlistsSelected ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="flex items-center gap-2 mb-4">
              <input
                type="text"
                placeholder="Search watchlists..."
                value={searchWatchlist}
                onChange={e => setSearchWatchlist(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
              />
              <div className="flex gap-1">
                <button
                  onClick={() => setWatchlistFilter('all')}
                  className={`px-3 py-2 text-xs rounded-lg transition-colors whitespace-nowrap ${watchlistFilter === 'all' ? 'bg-cyan-100 text-cyan-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  All ({watchlists.length})
                </button>
                <button
                  onClick={() => setWatchlistFilter('selected')}
                  className={`px-3 py-2 text-xs rounded-lg transition-colors whitespace-nowrap ${watchlistFilter === 'selected' ? 'bg-cyan-100 text-cyan-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  Selected ({selectedWatchlists.length})
                </button>
              </div>
            </div>

            <div className="space-y-2 max-h-[calc(100vh-420px)] overflow-y-auto">
              {filteredWatchlists.length === 0 ? (
                <p className="text-gray-400 text-center py-8 text-sm">No watchlists found</p>
              ) : filteredWatchlists.map(w => (
                <label key={w.id} className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors">
                  <input
                    type="checkbox"
                    checked={selectedWatchlists.includes(w.id)}
                    onChange={() => toggleWatchlist(w.id)}
                    className="mt-0.5 h-4 w-4 accent-cyan-600 rounded"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 text-sm">{w.name}</div>
                    {w.description && <div className="text-xs text-gray-500">{w.description}</div>}
                    <div className="text-xs text-gray-400 mt-0.5">{w.product_count} products</div>
                  </div>
                </label>
              ))}
            </div>
          </section>

          {/* Locations */}
          <section className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-blue-600" />
                Makro Postal Zones
              </h2>
              <button onClick={toggleAllLocations} className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                {allLocationsSelected ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="flex items-center gap-2 mb-4">
              <input
                type="text"
                placeholder="Search by name or postal code..."
                value={searchLocation}
                onChange={e => setSearchLocation(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
              />
              <div className="flex gap-1">
                <button
                  onClick={() => setLocationFilter('all')}
                  className={`px-3 py-2 text-xs rounded-lg transition-colors whitespace-nowrap ${locationFilter === 'all' ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  All ({locations.length})
                </button>
                <button
                  onClick={() => setLocationFilter('selected')}
                  className={`px-3 py-2 text-xs rounded-lg transition-colors whitespace-nowrap ${locationFilter === 'selected' ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  Selected ({selectedLocations.length})
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 max-h-[calc(100vh-420px)] overflow-y-auto">
              {filteredLocations.length === 0 ? (
                <p className="text-gray-400 text-center py-8 text-sm col-span-2">No locations found</p>
              ) : filteredLocations.map(l => (
                <label key={l.id} className="flex items-center gap-2 p-2.5 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors">
                  <input
                    type="checkbox"
                    checked={selectedLocations.includes(l.id)}
                    onChange={() => toggleLocation(l.id)}
                    className="h-4 w-4 accent-blue-600 rounded flex-shrink-0"
                  />
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">{l.name}</div>
                    <div className="text-xs text-gray-400">{l.branch_code}</div>
                  </div>
                </label>
              ))}
            </div>
          </section>
        </div>
      </div>
    </MainLayout>
  );
}
