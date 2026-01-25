'use client';

import { useState, useEffect, useRef } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Plus, Trash2, FolderOpen, Search, X, CheckCircle, Package, Upload, Download, ChevronDown, Check } from 'lucide-react';
import { apiFetch } from '@/lib/api';

// Multi-select dropdown component with search
function MultiSelect({
  options,
  selected,
  onChange,
  placeholder,
  className = '',
}: {
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder: string;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const toggleOption = (option: string) => {
    if (selected.includes(option)) {
      onChange(selected.filter(s => s !== option));
    } else {
      onChange([...selected, option]);
    }
  };

  const clearAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange([]);
  };

  // Filter options based on search term
  const filteredOptions = options.filter(option =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-white text-left flex items-center justify-between gap-2"
      >
        <span className={`truncate ${selected.length === 0 ? 'text-gray-500' : 'text-gray-900'}`}>
          {selected.length === 0
            ? placeholder
            : selected.length === 1
            ? selected[0]
            : `${selected.length} selected`}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {selected.length > 0 && (
            <button
              onClick={clearAll}
              className="p-0.5 hover:bg-gray-200 rounded"
            >
              <X className="w-3.5 h-3.5 text-gray-500" />
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg">
          {/* Search input */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          </div>

          {/* Options list */}
          <div className="max-h-60 overflow-y-auto">
            {filteredOptions.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-500 text-center">
                No options found
              </div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => toggleOption(option)}
                  className={`w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between ${
                    selected.includes(option) ? 'bg-cyan-50' : ''
                  }`}
                >
                  <span className="text-sm text-gray-900 truncate">{option}</span>
                  {selected.includes(option) && (
                    <Check className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface Product {
  sku: string;
  name: string;
  brand: string | null;
  category: string;
  price: number | null;
  image_url: string | null;
  added_at?: string;
}

interface SkuGroup {
  group_id: number;
  name: string;
  created_at: string;
  updated_at: string;
  products: Product[];
  product_count: number;
}

interface AvailableProduct {
  sku: string;
  name: string;
  brand: string | null;
  category: string;
  price: number | null;
  image_url: string | null;
}

export default function WatchlistSkuGroupsPage() {
  const [groups, setGroups] = useState<SkuGroup[]>([]);
  const [availableProducts, setAvailableProducts] = useState<AvailableProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddProductModal, setShowAddProductModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<SkuGroup | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [newGroupName, setNewGroupName] = useState('');
  const [importing, setImporting] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [exportingGroupId, setExportingGroupId] = useState<number | null>(null);
  
  // Filter states
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [allBrands, setAllBrands] = useState<string[]>([]);
  const [allCategories, setAllCategories] = useState<string[]>([]);

  const fetchGroups = async () => {
    try {
      const response = await apiFetch('/api/watchlist/sku-groups');
      if (response.ok) {
        const data = await response.json();
        setGroups(data.groups || []);
      }
    } catch (error) {
      console.error('Error fetching SKU groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableProducts = async () => {
    try {
      const params = new URLSearchParams({
        search: searchTerm,
        limit: '500',
      });
      
      if (selectedBrands.length > 0) {
        params.set('brand', selectedBrands.join(','));
      }
      if (selectedCategories.length > 0) {
        params.set('category', selectedCategories.join(','));
      }
      
      const response = await apiFetch(
        `/api/watchlist/products/available?${params.toString()}`
      );
      if (response.ok) {
        const data = await response.json();
        setAvailableProducts(data.products || []);
        
        // Extract unique brands and categories from all products
        const products = data.products || [];
        const brands = Array.from(new Set(products.map((p: AvailableProduct) => p.brand).filter(Boolean))).sort();
        const categories = Array.from(new Set(products.map((p: AvailableProduct) => p.category).filter(Boolean))).sort();
        setAllBrands(brands as string[]);
        setAllCategories(categories as string[]);
      }
    } catch (error) {
      console.error('Error fetching available products:', error);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  useEffect(() => {
    if (showAddProductModal) {
      fetchAvailableProducts();
    }
  }, [showAddProductModal, searchTerm, selectedBrands, selectedCategories]);

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      alert('Please provide a group name');
      return;
    }

    try {
      const response = await apiFetch('/api/watchlist/sku-groups', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newGroupName.trim(),
        }),
      });

      if (response.ok) {
        setShowCreateModal(false);
        setNewGroupName('');
        fetchGroups();
      } else {
        const error = await response.json();
        console.error('Error response:', error);
        alert(typeof error === 'string' ? error : error.detail || JSON.stringify(error) || 'Failed to create group');
      }
    } catch (error) {
      console.error('Error creating group:', error);
      alert(`Failed to create group: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDeleteGroup = async (groupId: number) => {
    if (!confirm('Are you sure you want to delete this group?')) return;

    try {
      const response = await apiFetch(`/api/watchlist/sku-groups/${groupId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchGroups();
      } else {
        alert('Failed to delete group');
      }
    } catch (error) {
      console.error('Error deleting group:', error);
      alert('Failed to delete group');
    }
  };

  const handleAddProduct = async (sku: string) => {
    if (!selectedGroup) return;

    try {
      const response = await apiFetch(
        `/api/watchlist/sku-groups/${selectedGroup.group_id}/products`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ sku }),
        }
      );

      if (response.ok) {
        // Refetch groups to update the UI
        const groupsResponse = await apiFetch('/api/watchlist/sku-groups');
        if (groupsResponse.ok) {
          const data = await groupsResponse.json();
          setGroups(data.groups || []);
          
          // Update selectedGroup with fresh data
          const updatedGroup = data.groups.find((g: SkuGroup) => g.group_id === selectedGroup.group_id);
          if (updatedGroup) {
            setSelectedGroup(updatedGroup);
          }
        }
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to add product to group');
      }
    } catch (error) {
      console.error('Error adding product:', error);
      alert('Failed to add product to group');
    }
  };

  const handleRemoveProduct = async (groupId: number, sku: string) => {
    try {
      const response = await apiFetch(
        `/api/watchlist/sku-groups/${groupId}/products/${encodeURIComponent(sku)}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        const error = await response.json();
        console.error('Error removing product:', error);
        throw new Error(error.detail || 'Failed to remove product');
      }
      
      // Refetch groups to update the UI
      const groupsResponse = await apiFetch('/api/watchlist/sku-groups');
      if (groupsResponse.ok) {
        const data = await groupsResponse.json();
        setGroups(data.groups || []);
        
        // Update selectedGroup if modal is open
        if (selectedGroup && selectedGroup.group_id === groupId) {
          const updatedGroup = data.groups.find((g: SkuGroup) => g.group_id === groupId);
          if (updatedGroup) {
            setSelectedGroup(updatedGroup);
          }
        }
      }
    } catch (error) {
      console.error('Error removing product:', error);
      alert(error instanceof Error ? error.message : 'Failed to remove product from group');
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImporting(true);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/watchlist/sku-groups/import-excel', {
        method: 'POST',
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setImportResult(result);
        setShowImportModal(true);
        fetchGroups();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to import Excel file');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file');
    } finally {
      setImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const filteredProducts = availableProducts.filter((prod) =>
    prod.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    prod.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleExportGroup = async (group: SkuGroup) => {
    setExportingGroupId(group.group_id);
    try {
      const response = await apiFetch(`/api/watchlist/sku-groups/${group.group_id}/export`);
      if (!response.ok) {
        throw new Error('Failed to export group');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const now = new Date();
      const timestamp = now.getFullYear().toString() +
        (now.getMonth() + 1).toString().padStart(2, '0') +
        now.getDate().toString().padStart(2, '0') + '_' +
        now.getHours().toString().padStart(2, '0') +
        now.getMinutes().toString().padStart(2, '0') +
        now.getSeconds().toString().padStart(2, '0');
      link.download = `${group.name}_export_${timestamp}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting group:', error);
      alert('Failed to export group');
    } finally {
      setExportingGroupId(null);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Watchlist SKU</h1>
            <p className="text-gray-500 mt-1">Track individual products by SKU</p>
          </div>
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={importing}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Upload className="w-5 h-5" />
              {importing ? 'Importing...' : 'Import Excel'}
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Create Group
            </button>
          </div>
        </div>

        {/* Groups Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600"></div>
          </div>
        ) : groups.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No SKU groups yet</h3>
            <p className="text-gray-500 mb-4">Create your first group to start tracking products</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
            >
              <Plus className="w-5 h-5" />
              Create Group
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {groups.map((group) => (
              <div
                key={group.group_id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="p-6 flex items-center justify-between gap-6">
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold text-gray-900 mb-1">
                          {group.name}
                        </h3>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Package className="w-4 h-4" />
                      <span>{group.product_count} products</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleExportGroup(group)}
                      disabled={exportingGroupId === group.group_id || group.product_count === 0}
                      className="px-6 py-2 border border-green-600 text-green-600 rounded-lg hover:bg-green-50 transition-colors flex items-center gap-2 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Export SKUs to Excel"
                    >
                      <Download className="w-4 h-4" />
                      {exportingGroupId === group.group_id ? 'Exporting...' : 'Export'}
                    </button>

                    <button
                      onClick={() => {
                        setSelectedGroup(group);
                        setShowAddProductModal(true);
                        setSearchTerm('');
                      }}
                      className="px-6 py-2 border border-cyan-600 text-cyan-600 rounded-lg hover:bg-cyan-50 transition-colors flex items-center gap-2 whitespace-nowrap"
                    >
                      <Plus className="w-4 h-4" />
                      Manage Products
                    </button>
                    
                    <button
                      onClick={() => handleDeleteGroup(group.group_id)}
                      className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete group"
                    >
                      <Trash2 className="w-5 h-5 text-red-600" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Group Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-100 bg-opacity-30 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Create New SKU Group</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Group Name *
                  </label>
                  <input
                    type="text"
                    value={newGroupName}
                    onChange={(e) => setNewGroupName(e.target.value)}
                    placeholder="e.g., Door Hardware"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewGroupName('');
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateGroup}
                  className="flex-1 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
                >
                  Create Group
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Add Product Modal */}
        {showAddProductModal && selectedGroup && (
          <div className="fixed inset-0 bg-white z-50 flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 bg-white">
              <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                      Manage Products for {selectedGroup.name}
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                      {selectedGroup.products.length} products added
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setShowAddProductModal(false);
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
                {/* Left Side - Added Products */}
                <div className="w-1/3 border-r border-gray-200 flex flex-col">
                  <div className="px-6 py-4 bg-green-50 border-b border-green-200">
                    <h3 className="font-semibold text-green-900 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Added Products
                    </h3>
                    <p className="text-sm text-green-700 mt-1">
                      {selectedGroup.products.length} in this group
                    </p>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4">
                    {selectedGroup.products.length === 0 ? (
                      <p className="text-gray-500 text-center py-8 text-sm">
                        No products added yet
                      </p>
                    ) : (
                      <div className="space-y-1">
                        {selectedGroup.products
                          .sort((a, b) => a.sku.localeCompare(b.sku))
                          .map((product) => (
                          <div
                            key={product.sku}
                            className="flex items-center gap-2 px-3 py-2 bg-white border-b border-gray-200 hover:bg-gray-50 transition-colors"
                          >
                            {product.image_url && (
                              <img
                                src={product.image_url}
                                alt={product.name}
                                className="w-8 h-8 object-cover rounded flex-shrink-0"
                              />
                            )}
                            <div className="text-sm font-mono text-gray-900 w-18 flex-shrink-0">
                              {product.sku}
                            </div>
                            <div className="text-sm text-gray-800 w-12 flex-shrink-0">
                              {product.price ? `฿${product.price.toLocaleString()}` : '-'}
                            </div>
                            <div className="flex-1 min-w-0 text-sm text-gray-900 truncate">
                              {product.name}
                            </div>
                            <button
                              onClick={() => handleRemoveProduct(selectedGroup.group_id, product.sku)}
                              className="p-1 hover:bg-gray-200 rounded transition-colors flex-shrink-0"
                              title="Remove product"
                            >
                              <Trash2 className="w-4 h-4 text-gray-700" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Side - Available Products */}
                <div className="flex-1 flex flex-col">
                  <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                    <h3 className="font-semibold text-gray-900 mb-3">Available Products</h3>
                    
                    {/* Search and Filters in one row */}
                    <div className="grid grid-cols-12 gap-3">
                      <div className="col-span-6 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                        <input
                          type="text"
                          placeholder="Search by name or SKU..."
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                        />
                      </div>
                      <div className="col-span-3">
                        <MultiSelect
                          options={allBrands}
                          selected={selectedBrands}
                          onChange={setSelectedBrands}
                          placeholder="All Brands"
                        />
                      </div>
                      <div className="col-span-3">
                        <MultiSelect
                          options={allCategories}
                          selected={selectedCategories}
                          onChange={setSelectedCategories}
                          placeholder="All Categories"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Products List */}
                  <div className="flex-1 overflow-y-auto p-4">
                    {filteredProducts.length === 0 ? (
                      <p className="text-gray-500 text-center py-8">No products found</p>
                    ) : (
                      <div className="space-y-1">
                        {filteredProducts
                          .filter(prod => !selectedGroup.products.some(p => p.sku === prod.sku))
                          .sort((a, b) => a.sku.localeCompare(b.sku))
                          .map((product) => (
                            <button
                              key={product.sku}
                              onClick={() => handleAddProduct(product.sku)}
                              className="w-full text-left flex items-center gap-2 px-3 py-2 bg-white border-b border-gray-200 hover:bg-cyan-50 transition-colors"
                            >
                              {product.image_url && (
                                <img
                                  src={product.image_url}
                                  alt={product.name}
                                  className="w-8 h-8 object-cover rounded flex-shrink-0"
                                />
                              )}
                              <div className="text-sm font-mono text-gray-900 w-24 flex-shrink-0">
                                {product.sku}
                              </div>
                              <div className="text-sm text-gray-800 w-20 flex-shrink-0">
                                {product.price ? `฿${product.price.toLocaleString()}` : '-'}
                              </div>
                              <div className="flex-1 min-w-0 text-sm text-gray-900 truncate">
                                {product.name}
                              </div>
                              <Plus className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            </button>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
          </div>
        )}

        {/* Import Result Modal */}
        {showImportModal && importResult && (
          <div className="fixed inset-0 bg-gray-100 bg-opacity-30 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl border border-gray-200 w-full max-w-3xl max-h-[85vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">Import Results</h2>
                  <button
                    onClick={() => {
                      setShowImportModal(false);
                      setImportResult(null);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-6 h-6 text-gray-500" />
                  </button>
                </div>

                {/* Summary */}
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-900 mb-2">Summary</h3>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="text-blue-700">Total Rows:</span>
                        <span className="font-medium ml-2">{importResult.total_rows}</span>
                      </div>
                      <div>
                        <span className="text-blue-700">Groups Processed:</span>
                        <span className="font-medium ml-2">{importResult.groups_processed}</span>
                      </div>
                    </div>
                  </div>

                  {/* Groups Created */}
                  {importResult.groups_created.length > 0 && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h3 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5" />
                        Groups Created ({importResult.groups_created.length})
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {importResult.groups_created.map((group: string) => (
                          <span key={group} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                            {group}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Groups Updated */}
                  {importResult.groups_updated.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h3 className="font-semibold text-yellow-900 mb-2">
                        Groups Updated ({importResult.groups_updated.length})
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {importResult.groups_updated.map((group: string) => (
                          <span key={group} className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
                            {group}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* SKUs Added */}
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-3">SKUs Added by Group</h3>
                    <div className="space-y-2 text-sm max-h-60 overflow-y-auto">
                      {Object.entries(importResult.skus_added).map(([group, stats]: [string, any]) => (
                        <div key={group} className="flex items-center justify-between py-2 border-b border-gray-200 last:border-0">
                          <span className="font-medium text-gray-700">{group}</span>
                          <div className="flex gap-4 text-xs">
                            <span className="text-green-600">✓ {stats.added} added</span>
                            {stats.already_exists > 0 && (
                              <span className="text-gray-500">⚠ {stats.already_exists} existed</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* SKUs Not Found */}
                  {Object.keys(importResult.skus_not_found).length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <h3 className="font-semibold text-red-900 mb-3">
                        SKUs Not Found in Database
                      </h3>
                      <div className="space-y-3 text-sm max-h-60 overflow-y-auto">
                        {Object.entries(importResult.skus_not_found).map(([group, skus]: [string, any]) => (
                          <div key={group}>
                            <div className="font-medium text-red-800 mb-1">{group}</div>
                            <div className="pl-3 text-red-700 text-xs space-y-1">
                              {skus.slice(0, 10).map((sku: string, idx: number) => (
                                <div key={idx}>• {sku}</div>
                              ))}
                              {skus.length > 10 && (
                                <div className="text-red-600 italic">
                                  ...and {skus.length - 10} more
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <button
                  onClick={() => {
                    setShowImportModal(false);
                    setImportResult(null);
                  }}
                  className="w-full mt-6 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
