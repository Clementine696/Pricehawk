'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/layout/MainLayout';
import { apiFetch } from '@/lib/api';
import { MapPin, Package, CheckCircle2, Loader2, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface Location {
  location_id: number;
  retailer_id: string;
  name_th: string;
  name_en: string | null;
  branch_code: string;
  postal_code: string | null;
}

interface SdeptGroup {
  group_id: number;
  sdept: string;
  description: string | null;
  product_count: number;
}

export default function PriceByLocationSettingsPage() {
  // State
  const [locations, setLocations] = useState<Location[]>([]);
  const [groups, setGroups] = useState<SdeptGroup[]>([]);
  const [selectedLocations, setSelectedLocations] = useState<number[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchLocation, setSearchLocation] = useState('');
  const [searchGroup, setSearchGroup] = useState('');
  const [groupFilter, setGroupFilter] = useState<'all' | 'selected'>('all');
  const [locationFilter, setLocationFilter] = useState<'all' | 'selected'>('all');

  // Fetch data on mount
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    setError('');

    try {
      // Fetch all locations (GlobalHouse only)
      const locationsRes = await apiFetch('/api/locations?retailer_id=gbh');
      if (!locationsRes.ok) throw new Error('Failed to fetch locations');
      const locationsData = await locationsRes.json();
      setLocations(locationsData);

      // Fetch available S-dept groups
      const groupsRes = await apiFetch('/api/location-watch/available-groups');
      if (!groupsRes.ok) throw new Error('Failed to fetch groups');
      const groupsData = await groupsRes.json();
      setGroups(groupsData);

      // Fetch currently monitored locations
      const monitoredLocationsRes = await apiFetch('/api/location-watch/monitored-locations');
      if (!monitoredLocationsRes.ok) throw new Error('Failed to fetch monitored locations');
      const monitoredLocationsData = await monitoredLocationsRes.json();
      setSelectedLocations(monitoredLocationsData.map((l: any) => l.location_id));

      // Fetch currently monitored groups
      const monitoredGroupsRes = await apiFetch('/api/location-watch/monitored-groups');
      if (!monitoredGroupsRes.ok) throw new Error('Failed to fetch monitored groups');
      const monitoredGroupsData = await monitoredGroupsRes.json();
      setSelectedGroups(monitoredGroupsData.map((g: any) => g.group_id));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocationToggle = (locationId: number) => {
    setSelectedLocations(prev =>
      prev.includes(locationId)
        ? prev.filter(id => id !== locationId)
        : [...prev, locationId]
    );
  };

  const handleGroupToggle = (groupId: number) => {
    setSelectedGroups(prev =>
      prev.includes(groupId)
        ? prev.filter(id => id !== groupId)
        : [...prev, groupId]
    );
  };

  const handleSelectAllLocations = () => {
    const filtered = filteredLocations;
    const allSelected = filtered.every(l => selectedLocations.includes(l.location_id));

    if (allSelected) {
      // Deselect all filtered
      setSelectedLocations(prev => prev.filter(id => !filtered.some(l => l.location_id === id)));
    } else {
      // Select all filtered
      const newIds = filtered.map(l => l.location_id);
      setSelectedLocations(prev => Array.from(new Set([...prev, ...newIds])));
    }
  };

  const handleSelectAllGroups = () => {
    const filtered = filteredGroups;
    const allSelected = filtered.every(g => selectedGroups.includes(g.group_id));

    if (allSelected) {
      // Deselect all filtered
      setSelectedGroups(prev => prev.filter(id => !filtered.some(g => g.group_id === id)));
    } else {
      // Select all filtered
      const newIds = filtered.map(g => g.group_id);
      setSelectedGroups(prev => Array.from(new Set([...prev, ...newIds])));
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    setSuccess('');

    try {
      // Save monitored groups
      const groupsRes = await apiFetch('/api/location-watch/monitored-groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ group_ids: selectedGroups }),
      });

      if (!groupsRes.ok) {
        const data = await groupsRes.json();
        throw new Error(data.detail || 'Failed to save groups');
      }

      // Save monitored locations
      const locationsRes = await apiFetch('/api/location-watch/monitored-locations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location_ids: selectedLocations }),
      });

      if (!locationsRes.ok) {
        const data = await locationsRes.json();
        throw new Error(data.detail || 'Failed to save locations');
      }

      setSuccess('Settings saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  // Filter locations by search and selected filter
  const filteredLocations = locations.filter(loc => {
    const matchesSearch = searchLocation === '' ||
      loc.name_th.toLowerCase().includes(searchLocation.toLowerCase()) ||
      (loc.name_en && loc.name_en.toLowerCase().includes(searchLocation.toLowerCase())) ||
      loc.branch_code.toLowerCase().includes(searchLocation.toLowerCase()) ||
      (loc.postal_code && loc.postal_code.toLowerCase().includes(searchLocation.toLowerCase()));
    
    const matchesFilter = locationFilter === 'all' || selectedLocations.includes(loc.location_id);
    
    return matchesSearch && matchesFilter;
  });

  // Filter groups by search and selected filter
  const filteredGroups = groups.filter(group => {
    const matchesSearch = searchGroup === '' ||
      group.sdept.toLowerCase().includes(searchGroup.toLowerCase()) ||
      (group.description && group.description.toLowerCase().includes(searchGroup.toLowerCase()));
    
    const matchesFilter = groupFilter === 'all' || selectedGroups.includes(group.group_id);
    
    return matchesSearch && matchesFilter;
  });

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Back link */}
        <Link href="/price-by-location" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4" />
          Back to Price by Location
        </Link>

        {/* Header with Action Button */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Price by Location Settings
            </h1>
            <p className="text-gray-600">
              Configure which product groups and locations to monitor for location-based pricing
            </p>
          </div>
          
          {/* Action Button */}
          <Button
            variant="primary"
            onClick={handleSave}
            loading={isSaving}
            disabled={isSaving || (selectedGroups.length === 0 && selectedLocations.length === 0)}
          >
            Save Settings
          </Button>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5" />
            {success}
          </div>
        )}

        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="bg-cyan-500 p-3 rounded-lg">
                <Package className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Selected Groups</p>
                <p className="text-2xl font-bold text-gray-900">{selectedGroups.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="bg-blue-500 p-3 rounded-lg">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Selected Locations</p>
                <p className="text-2xl font-bold text-gray-900">{selectedLocations.length}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Product Groups Section */}
          <section className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <Package className="h-5 w-5 text-blue-600" />
                Product Groups
              </h2>
              <button
                onClick={handleSelectAllGroups}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                {filteredGroups.every(g => selectedGroups.includes(g.group_id))
                  ? 'Deselect All'
                  : 'Select All'}
              </button>
            </div>

            {/* Search and Filter */}
            <div className="flex items-center gap-3 mb-4">
              <input
                type="text"
                placeholder="Search groups..."
                value={searchGroup}
                onChange={(e) => setSearchGroup(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => setGroupFilter('all')}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors whitespace-nowrap ${
                    groupFilter === 'all'
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  All ({groups.length})
                </button>
                <button
                  onClick={() => setGroupFilter('selected')}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors whitespace-nowrap ${
                    groupFilter === 'selected'
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Selected ({selectedGroups.length})
                </button>
              </div>
            </div>

            {/* Groups List */}
            <div className="space-y-2 max-h-[calc(100vh-380px)] overflow-y-auto">
              {filteredGroups.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No groups found</p>
              ) : (
                filteredGroups.map((group) => (
                  <label
                    key={group.group_id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedGroups.includes(group.group_id)}
                      onChange={() => handleGroupToggle(group.group_id)}
                      className="mt-1 h-4 w-4 accent-blue-600 rounded focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {group.sdept}
                      </div>
                      {group.description && (
                        <div className="text-sm text-gray-600">
                          {group.description}
                        </div>
                      )}
                      <div className="text-xs text-gray-500 mt-1">
                        {group.product_count} products
                      </div>
                    </div>
                  </label>
                ))
              )}
            </div>
          </section>

          {/* Locations Section */}
          <section className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-blue-600" />
                Locations
              </h2>
              <button
                onClick={handleSelectAllLocations}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                {filteredLocations.every(l => selectedLocations.includes(l.location_id))
                  ? 'Deselect All'
                  : 'Select All'}
              </button>
            </div>

            {/* Search and Filter */}
            <div className="flex items-center gap-3 mb-4">
              <input
                type="text"
                placeholder="Search locations..."
                value={searchLocation}
                onChange={(e) => setSearchLocation(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => setLocationFilter('all')}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors whitespace-nowrap ${
                    locationFilter === 'all'
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  All ({locations.length})
                </button>
                <button
                  onClick={() => setLocationFilter('selected')}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors whitespace-nowrap ${
                    locationFilter === 'selected'
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Selected ({selectedLocations.length})
                </button>
              </div>
            </div>

            {/* Locations List */}
            {locationFilter === 'selected' ? (
              /* Compact 2-column grid for Selected view */
              <div className="grid grid-cols-2 gap-3 max-h-[calc(100vh-380px)] overflow-y-auto">
                {filteredLocations.length === 0 ? (
                  <p className="text-gray-500 text-center py-8 col-span-2">No locations found</p>
                ) : (
                  filteredLocations.map((location) => (
                    <label
                      key={location.location_id}
                      className="flex items-center gap-2 p-2 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedLocations.includes(location.location_id)}
                        onChange={() => handleLocationToggle(location.location_id)}
                        className="h-4 w-4 accent-blue-600 rounded focus:ring-blue-500 flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {location.name_th}
                        </div>
                      </div>
                      {location.postal_code && (
                        <div className="text-xs text-gray-500 flex-shrink-0">
                          {location.postal_code}
                        </div>
                      )}
                    </label>
                  ))
                )}
              </div>
            ) : (
              /* Regular list view for All */
              <div className="space-y-2 max-h-[calc(100vh-380px)] overflow-y-auto">
                {filteredLocations.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No locations found</p>
                ) : (
                  filteredLocations.map((location) => (
                    <label
                      key={location.location_id}
                      className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedLocations.includes(location.location_id)}
                        onChange={() => handleLocationToggle(location.location_id)}
                        className="mt-1 h-4 w-4 accent-blue-600 rounded focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">
                          {location.name_th}
                        </div>
                        {location.name_en && (
                          <div className="text-sm text-gray-600">
                            {location.name_en}
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">
                          {location.branch_code}{location.postal_code ? ` · ${location.postal_code}` : ''}
                        </div>
                      </div>
                    </label>
                  ))
                )}
              </div>
            )}
          </section>
        </div>
      </div>
    </MainLayout>
  );
}
