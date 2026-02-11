'use client';

import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { apiFetch } from '@/lib/api';
import { MapPin, Package, CheckCircle2, Loader2 } from 'lucide-react';

interface Location {
  location_id: number;
  location_code: string;
  name_th: string;
  name_en: string;
  province_th: string;
  province_en: string;
  retailer_id: string;
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
      setSelectedLocations(prev => [...new Set([...prev, ...newIds])]);
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
      setSelectedGroups(prev => [...new Set([...prev, ...newIds])]);
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

  // Filter locations by search
  const filteredLocations = locations.filter(loc =>
    searchLocation === '' ||
    loc.name_th.toLowerCase().includes(searchLocation.toLowerCase()) ||
    loc.name_en.toLowerCase().includes(searchLocation.toLowerCase()) ||
    loc.province_th.toLowerCase().includes(searchLocation.toLowerCase()) ||
    loc.location_code.toLowerCase().includes(searchLocation.toLowerCase())
  );

  // Filter groups by search
  const filteredGroups = groups.filter(group =>
    searchGroup === '' ||
    group.sdept.toLowerCase().includes(searchGroup.toLowerCase()) ||
    (group.description && group.description.toLowerCase().includes(searchGroup.toLowerCase()))
  );

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
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Price by Location Settings
          </h1>
          <p className="text-gray-600">
            Configure which product groups and locations to monitor for location-based pricing
          </p>
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <Package className="h-8 w-8 text-cyan-600" />
              <div>
                <p className="text-sm text-gray-600">Selected Groups</p>
                <p className="text-2xl font-bold text-cyan-600">{selectedGroups.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <MapPin className="h-8 w-8 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Selected Locations</p>
                <p className="text-2xl font-bold text-blue-600">{selectedLocations.length}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Product Groups Section */}
          <section className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <Package className="h-5 w-5 text-cyan-600" />
                Product Groups
              </h2>
              <button
                onClick={handleSelectAllGroups}
                className="text-sm text-cyan-600 hover:text-cyan-700 font-medium"
              >
                {filteredGroups.every(g => selectedGroups.includes(g.group_id))
                  ? 'Deselect All'
                  : 'Select All'}
              </button>
            </div>

            {/* Search */}
            <input
              type="text"
              placeholder="Search groups..."
              value={searchGroup}
              onChange={(e) => setSearchGroup(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />

            {/* Groups List */}
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
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
                      className="mt-1 h-4 w-4 text-cyan-600 rounded focus:ring-cyan-500"
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
          <section className="bg-white border border-gray-200 rounded-lg p-6">
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

            {/* Search */}
            <input
              type="text"
              placeholder="Search locations..."
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            {/* Locations List */}
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
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
                      className="mt-1 h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {location.name_th}
                      </div>
                      <div className="text-sm text-gray-600">
                        {location.name_en}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {location.province_th} • {location.location_code}
                      </div>
                    </div>
                  </label>
                ))
              )}
            </div>
          </section>
        </div>

        {/* Save Button */}
        <div className="mt-6 flex justify-end gap-4">
          <button
            onClick={() => window.location.href = '/price-by-location'}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || (selectedGroups.length === 0 && selectedLocations.length === 0)}
            className="px-6 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </MainLayout>
  );
}
