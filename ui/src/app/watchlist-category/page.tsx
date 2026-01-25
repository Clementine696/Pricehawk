'use client';

import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Plus, Trash2, FolderOpen, Tag, Search, X, CheckCircle } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface Category {
  category: string;
  product_count: number;
  added_at?: string;
}

interface WatchlistGroup {
  group_id: number;
  name: string;
  display_name: string;
  description: string;
  categories: Category[];
  total_categories: number;
  created_at: string;
}

interface AvailableCategory {
  category: string;
  product_count: number;
}

export default function WatchlistGroupsPage() {
  const [groups, setGroups] = useState<WatchlistGroup[]>([]);
  const [availableCategories, setAvailableCategories] = useState<AvailableCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddCategoryModal, setShowAddCategoryModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<WatchlistGroup | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Form states
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDisplayName, setNewGroupDisplayName] = useState('');
  const [newGroupDescription, setNewGroupDescription] = useState('');

  useEffect(() => {
    fetchGroups();
    fetchAvailableCategories();
  }, []);

  const fetchGroups = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch('/api/watchlist/groups');
      if (!response.ok) throw new Error('Failed to fetch groups');
      const data = await response.json();
      setGroups(data.groups || []);
    } catch (error) {
      console.error('Error fetching groups:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAvailableCategories = async () => {
    try {
      const response = await apiFetch('/api/watchlist/categories/available');
      if (!response.ok) throw new Error('Failed to fetch categories');
      const data = await response.json();
      setAvailableCategories(data.categories || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName || !newGroupDisplayName) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      const response = await apiFetch('/api/watchlist/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newGroupName,
          display_name: newGroupDisplayName,
          description: newGroupDescription,
        }),
      });

      if (!response.ok) throw new Error('Failed to create group');

      setShowCreateModal(false);
      setNewGroupName('');
      setNewGroupDisplayName('');
      setNewGroupDescription('');
      fetchGroups();
    } catch (error) {
      console.error('Error creating group:', error);
      alert('Failed to create watchlist group');
    }
  };

  const handleDeleteGroup = async (groupId: number, groupName: string) => {
    if (!confirm(`Are you sure you want to delete "${groupName}"?`)) return;

    try {
      const response = await apiFetch(`/api/watchlist/groups/${groupId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete group');
      fetchGroups();
    } catch (error) {
      console.error('Error deleting group:', error);
      alert('Failed to delete watchlist group');
    }
  };

  const handleAddCategory = async (category: string) => {
    if (!selectedGroup) return;

    try {
      const response = await apiFetch(
        `/api/watchlist/groups/${selectedGroup.group_id}/categories`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category }),
        }
      );

      if (!response.ok) throw new Error('Failed to add category');
      
      // Refresh groups and update selected group
      const groupsResponse = await apiFetch('/api/watchlist/groups');
      if (groupsResponse.ok) {
        const data = await groupsResponse.json();
        setGroups(data.groups || []);
        // Update selected group with fresh data
        const updatedGroup = data.groups.find(
          (g: WatchlistGroup) => g.group_id === selectedGroup.group_id
        );
        if (updatedGroup) {
          setSelectedGroup(updatedGroup);
        }
      }
    } catch (error) {
      console.error('Error adding category:', error);
      alert('Failed to add category to group');
    }
  };

  const handleRemoveCategory = async (category: string) => {
    if (!selectedGroup) return;

    try {
      const response = await apiFetch(
        `/api/watchlist/groups/${selectedGroup.group_id}/categories/${encodeURIComponent(category)}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        const error = await response.json();
        console.error('Error removing category:', error);
        throw new Error(error.detail || 'Failed to remove category');
      }
      
      // Refetch groups to update the UI
      const groupsResponse = await apiFetch('/api/watchlist/groups');
      if (groupsResponse.ok) {
        const data = await groupsResponse.json();
        setGroups(data.groups || []);
        
        // Update selectedGroup if modal is open
        const updatedGroup = data.groups.find((g: WatchlistGroup) => g.group_id === selectedGroup.group_id);
        if (updatedGroup) {
          setSelectedGroup(updatedGroup);
        }
      }
    } catch (error) {
      console.error('Error removing category:', error);
      alert(error instanceof Error ? error.message : 'Failed to remove category from group');
    }
  };

  const filteredCategories = availableCategories.filter((cat) =>
    cat.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Watchlist Category</h1>
            <p className="text-gray-600 mt-1">
              Manage global category groups - visible to all users
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
          >
            <Plus className="w-5 h-5" />
            New Group
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{groups.length}</div>
            <div className="text-sm text-gray-500">Watchlist Groups</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-cyan-600">
              {groups.reduce((sum, g) => sum + g.total_categories, 0)}
            </div>
            <div className="text-sm text-gray-500">Total Categories Watched</div>
          </div>
        </div>

        {/* Groups List */}
        {isLoading ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading groups...</p>
          </div>
        ) : groups.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <FolderOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No watchlist groups yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 text-cyan-500 hover:text-cyan-600"
            >
              Create your first group
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {groups.map((group) => (
              <div
                key={group.group_id}
                className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {group.display_name}
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">{group.description}</p>
                    </div>
                    <button
                      onClick={() => handleDeleteGroup(group.group_id, group.display_name)}
                      className="text-red-500 hover:text-red-600"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="flex items-center gap-2 mb-4">
                    <Tag className="w-4 h-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-700">
                      {group.total_categories} {group.total_categories === 1 ? 'category' : 'categories'}
                    </span>
                  </div>

                  {/* Categories */}
                  <div className="space-y-2 mb-4 max-h-48 overflow-y-auto">
                    {group.categories.length === 0 ? (
                      <p className="text-sm text-gray-400 italic">No categories yet</p>
                    ) : (
                      group.categories.map((cat) => (
                        <div
                          key={cat.category}
                          className="flex items-center justify-between bg-gray-50 rounded px-3 py-2"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {cat.category}
                            </p>
                            <p className="text-xs text-gray-500">
                              {cat.product_count} products
                            </p>
                          </div>
                          <button
                            onClick={() =>
                              handleRemoveCategory(cat.category)
                            }
                            className="ml-2 text-red-500 hover:text-red-600"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>

                  <button
                    onClick={() => {
                      setSelectedGroup(group);
                      setShowAddCategoryModal(true);
                    }}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-cyan-500 text-cyan-500 rounded-lg hover:bg-cyan-50 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Add Category
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Group Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Create Watchlist Group</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name (ID) *
                  </label>
                  <input
                    type="text"
                    value={newGroupName}
                    onChange={(e) => setNewGroupName(e.target.value)}
                    placeholder="e.g., glue_and_cement"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Lowercase, no spaces (use underscores)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Display Name *
                  </label>
                  <input
                    type="text"
                    value={newGroupDisplayName}
                    onChange={(e) => setNewGroupDisplayName(e.target.value)}
                    placeholder="e.g., Glue & Cement"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newGroupDescription}
                    onChange={(e) => setNewGroupDescription(e.target.value)}
                    placeholder="Brief description of this watchlist group"
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateGroup}
                  className="flex-1 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Add Category Modal */}
        {showAddCategoryModal && selectedGroup && (
          <div className="fixed inset-0 bg-gray-100 bg-opacity-30 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-6xl h-[85vh] flex flex-col">
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                      Manage Categories for {selectedGroup.display_name}
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                      {selectedGroup.categories.length} categories added
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setShowAddCategoryModal(false);
                      setSelectedGroup(null);
                      setSearchTerm('');
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-6 h-6 text-gray-500" />
                  </button>
                </div>
              </div>

              {/* Two Column Layout */}
              <div className="flex-1 flex overflow-hidden">
                {/* Left Side - Added Categories */}
                <div className="w-1/3 border-r border-gray-200 flex flex-col">
                  <div className="px-6 py-4 bg-green-50 border-b border-green-200">
                    <h3 className="font-semibold text-green-900 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Added Categories
                    </h3>
                    <p className="text-sm text-green-700 mt-1">
                      {selectedGroup.categories.length} in this group
                    </p>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {selectedGroup.categories.length === 0 ? (
                      <p className="text-gray-500 text-center py-8 text-sm">
                        No categories added yet
                      </p>
                    ) : (
                      selectedGroup.categories.map((cat) => (
                        <div
                          key={cat.category}
                          className="px-4 py-3 rounded-lg bg-green-50 border border-green-300"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <div className="font-medium text-green-900 text-sm">
                                {cat.category}
                              </div>
                              <div className="text-xs text-green-700 mt-1">
                                {cat.product_count} products
                              </div>
                            </div>
                            <button
                              onClick={() => handleRemoveCategory(cat.category)}
                              className="p-1 hover:bg-green-100 rounded transition-colors"
                              title="Remove category"
                            >
                              <Trash2 className="w-4 h-4 text-green-700" />
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Right Side - Available Categories */}
                <div className="flex-1 flex flex-col">
                  <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                    <h3 className="font-semibold text-gray-900 mb-3">Available Categories</h3>
                    {/* Search */}
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                      <input
                        type="text"
                        placeholder="Search categories..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  {/* Categories Grid */}
                  <div className="flex-1 overflow-y-auto p-6">
                    {filteredCategories.length === 0 ? (
                      <p className="text-gray-500 text-center py-8">No categories found</p>
                    ) : (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                        {filteredCategories
                          .filter(cat => !selectedGroup.categories.some(c => c.category === cat.category))
                          .map((cat) => (
                            <button
                              key={cat.category}
                              onClick={() => handleAddCategory(cat.category)}
                              className="text-left px-4 py-3 rounded-lg border-2 border-gray-300 bg-white hover:border-cyan-500 hover:bg-cyan-50 hover:shadow-md transition-all"
                            >
                              <div className="flex items-center justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium text-gray-900 mb-1">
                                    {cat.category}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    {cat.product_count} products
                                  </div>
                                </div>
                                <Plus className="w-5 h-5 text-gray-400 flex-shrink-0" />
                              </div>
                            </button>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
