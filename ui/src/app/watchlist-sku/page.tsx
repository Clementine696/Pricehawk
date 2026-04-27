"use client";

import { useState, useEffect, useRef } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import {
  Plus,
  Trash2,
  FolderOpen,
  Search,
  X,
  CheckCircle,
  Package,
  Upload,
  Download,
  ChevronDown,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { MultiSelect } from "@/components/ui/MultiSelect";
import { Button } from "@/components/ui/Button";

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
  const [availableProducts, setAvailableProducts] = useState<
    AvailableProduct[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddProductModal, setShowAddProductModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<SkuGroup | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [groupSearchTerm, setGroupSearchTerm] = useState("");
  const [newGroupName, setNewGroupName] = useState("");
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
  const [allExpanded, setAllExpanded] = useState(false);
  const detailsRefs = useRef<HTMLDetailsElement[]>([]);

  const fetchGroups = async () => {
    try {
      const response = await apiFetch("/api/watchlist/sku-groups");
      if (response.ok) {
        const data = await response.json();
        const sortedGroups = (data.groups || []).sort((a: SkuGroup, b: SkuGroup) => {
          return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
        });
        setGroups(sortedGroups);
      }
    } catch (error) {
      console.error("Error fetching SKU groups:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableProducts = async () => {
    try {
      const params = new URLSearchParams({
        search: searchTerm,
        limit: "500",
      });

      if (selectedBrands.length > 0) {
        params.set("brand", selectedBrands.join(","));
      }
      if (selectedCategories.length > 0) {
        params.set("category", selectedCategories.join(","));
      }

      const response = await apiFetch(
        `/api/watchlist/products/available?${params.toString()}`,
      );
      if (response.ok) {
        const data = await response.json();
        setAvailableProducts(data.products || []);

        // Extract unique brands and categories from all products
        const products = data.products || [];
        const brands = Array.from(
          new Set(
            products.map((p: AvailableProduct) => p.brand).filter(Boolean),
          ),
        ).sort();
        const categories = Array.from(
          new Set(
            products.map((p: AvailableProduct) => p.category).filter(Boolean),
          ),
        ).sort();
        setAllBrands(brands as string[]);
        setAllCategories(categories as string[]);
      }
    } catch (error) {
      console.error("Error fetching available products:", error);
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

  useEffect(() => {
    if (showImportModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showImportModal]);

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      alert("Please provide a group name");
      return;
    }

    try {
      const response = await apiFetch("/api/watchlist/sku-groups", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: newGroupName.trim(),
        }),
      });

      if (response.ok) {
        setShowCreateModal(false);
        setNewGroupName("");
        fetchGroups();
      } else {
        const error = await response.json();
        console.error("Error response:", error);
        alert(
          typeof error === "string"
            ? error
            : error.detail || JSON.stringify(error) || "Failed to create group",
        );
      }
    } catch (error) {
      console.error("Error creating group:", error);
      alert(
        `Failed to create group: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    }
  };

  const toggleAllDetails = () => {
    const newState = !allExpanded;
    setAllExpanded(newState);
    detailsRefs.current.forEach(details => {
      if (details) {
        details.open = newState;
      }
    });
  };

  const handleDeleteGroup = async (groupId: number) => {
    if (!confirm("Are you sure you want to delete this group?")) return;

    try {
      const response = await apiFetch(`/api/watchlist/sku-groups/${groupId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        fetchGroups();
      } else {
        alert("Failed to delete group");
      }
    } catch (error) {
      console.error("Error deleting group:", error);
      alert("Failed to delete group");
    }
  };

  const handleAddProduct = async (sku: string) => {
    if (!selectedGroup) return;

    try {
      const response = await apiFetch(
        `/api/watchlist/sku-groups/${selectedGroup.group_id}/products`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ sku }),
        },
      );

      if (response.ok) {
        // Refetch groups to update the UI
        const groupsResponse = await apiFetch("/api/watchlist/sku-groups");
        if (groupsResponse.ok) {
          const data = await groupsResponse.json();
          setGroups(data.groups || []);

          // Update selectedGroup with fresh data
          const updatedGroup = data.groups.find(
            (g: SkuGroup) => g.group_id === selectedGroup.group_id,
          );
          if (updatedGroup) {
            setSelectedGroup(updatedGroup);
          }
        }
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to add product to group");
      }
    } catch (error) {
      console.error("Error adding product:", error);
      alert("Failed to add product to group");
    }
  };

  const handleRemoveProduct = async (groupId: number, sku: string) => {
    try {
      const response = await apiFetch(
        `/api/watchlist/sku-groups/${groupId}/products/${encodeURIComponent(sku)}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        const error = await response.json();
        console.error("Error removing product:", error);
        throw new Error(error.detail || "Failed to remove product");
      }

      // Refetch groups to update the UI
      const groupsResponse = await apiFetch("/api/watchlist/sku-groups");
      if (groupsResponse.ok) {
        const data = await groupsResponse.json();
        setGroups(data.groups || []);

        // Update selectedGroup if modal is open
        if (selectedGroup && selectedGroup.group_id === groupId) {
          const updatedGroup = data.groups.find(
            (g: SkuGroup) => g.group_id === groupId,
          );
          if (updatedGroup) {
            setSelectedGroup(updatedGroup);
          }
        }
      }
    } catch (error) {
      console.error("Error removing product:", error);
      alert(
        error instanceof Error
          ? error.message
          : "Failed to remove product from group",
      );
    }
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) {
      console.log("No file selected");
      return;
    }

    console.log("=".repeat(60));
    console.log("EXCEL UPLOAD STARTED (Frontend)");
    console.log("=".repeat(60));
    console.log("File name:", file.name);
    console.log("File size:", file.size, "bytes", `(${(file.size / 1024).toFixed(2)} KB)`);
    console.log("File type:", file.type);

    setImporting(true);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      console.log("FormData created with file");

      const token = localStorage.getItem("auth_token");
      console.log("Auth token:", token ? "Present" : "Missing");

      console.log("Sending POST request to /api/watchlist/sku-groups/import-excel...");
      const response = await fetch("/api/watchlist/sku-groups/import-excel", {
        method: "POST",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: formData,
      });

      console.log("Response received:");
      console.log("- Status:", response.status);
      console.log("- Status Text:", response.statusText);
      console.log("- OK:", response.ok);

      if (response.ok) {
        console.log("Response OK, parsing JSON...");
        const result = await response.json();
        console.log("Import result:", result);
        setImportResult(result);
        setShowImportModal(true);
        fetchGroups();
        console.log("=".repeat(60));
        console.log("EXCEL UPLOAD COMPLETED SUCCESSFULLY (Frontend)");
        console.log("=".repeat(60));
      } else {
        console.log("Response NOT OK, parsing error...");
        const error = await response.json();
        console.error("Error response:", error);
        alert(error.detail || "Failed to import Excel file");
        console.log("=".repeat(60));
        console.log("EXCEL UPLOAD FAILED (Frontend) - Server Error");
        console.log("=".repeat(60));
      }
    } catch (error) {
      console.log("=".repeat(60));
      console.log("EXCEL UPLOAD FAILED (Frontend) - Exception Caught");
      console.log("=".repeat(60));
      console.error("Error uploading file:", error);
      console.error("Error type:", error instanceof Error ? error.constructor.name : typeof error);
      console.error("Error message:", error instanceof Error ? error.message : String(error));
      if (error instanceof Error && error.stack) {
        console.error("Error stack:", error.stack);
      }
      alert("Failed to upload file");
    } finally {
      setImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const filteredProducts = availableProducts.filter(
    (prod) =>
      prod.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prod.sku.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const handleExportGroup = async (group: SkuGroup) => {
    setExportingGroupId(group.group_id);
    try {
      const response = await apiFetch(
        `/api/watchlist/sku-groups/${group.group_id}/export`,
      );
      if (!response.ok) {
        throw new Error("Failed to export group");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const now = new Date();
      const timestamp =
        now.getFullYear().toString() +
        (now.getMonth() + 1).toString().padStart(2, "0") +
        now.getDate().toString().padStart(2, "0") +
        "_" +
        now.getHours().toString().padStart(2, "0") +
        now.getMinutes().toString().padStart(2, "0") +
        now.getSeconds().toString().padStart(2, "0");
      link.download = `${group.name}_export_${timestamp}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error exporting group:", error);
      alert("Failed to export group");
    } finally {
      setExportingGroupId(null);
    }
  };

  const handleExportNotFoundSkus = () => {
    if (!importResult || !importResult.skus_not_found) return;

    // Create CSV content
    let csvContent = 'Group,SKU\n';
    
    Object.entries(importResult.skus_not_found).forEach(([group, skus]: [string, any]) => {
      skus.forEach((sku: string) => {
        csvContent += `"${group}","${sku}"\n`;
      });
    });

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const now = new Date();
    const timestamp =
      now.getFullYear().toString() +
      (now.getMonth() + 1).toString().padStart(2, '0') +
      now.getDate().toString().padStart(2, '0') +
      '_' +
      now.getHours().toString().padStart(2, '0') +
      now.getMinutes().toString().padStart(2, '0') +
      now.getSeconds().toString().padStart(2, '0');
    link.download = `skus_not_found_${timestamp}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  return (
    <MainLayout>
      <div className="space-y-6 relative">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Watchlist</h1>
            <p className="text-gray-500 mt-1">
              Track products by sub-department
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              className="hidden"
            />
            <Button variant="outline" onClick={() => fileInputRef.current?.click()} disabled={importing} loading={importing} icon={<Upload className="w-5 h-5" />}>
              {importing ? "Importing..." : "Import Excel"}
            </Button>
            <Button variant="primary" onClick={() => setShowCreateModal(true)} icon={<Plus className="w-5 h-5" />}>
              Create Group
            </Button>
          </div>
        </div>

        {/* Import Result Banner */}
        {showImportModal && importResult && (
          <div className="bg-white rounded-2xl border border-gray-300 overflow-hidden shadow-sm">
            {/* Success Banner */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-white">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-full bg-emerald-100">
                  <CheckCircle className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">Import Completed</h2>
                  <p className="text-sm text-gray-600">File has been processed successfully</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setShowImportModal(false);
                  setImportResult(null);
                }}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Statistics */}
            <div className="p-6 border-b border-gray-200 bg-white">
              <div className="grid grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-900 mb-1">
                    {importResult?.total_rows?.toLocaleString() || 0}
                  </div>
                  <div className="text-xs text-gray-600 uppercase tracking-wide">Total Rows</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-emerald-600 mb-1">
                    {importResult?.groups_processed || 0}
                  </div>
                  <div className="text-xs text-gray-600 uppercase tracking-wide">Groups Processed</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-amber-600 mb-1">
                    {importResult?.groups_updated?.length || 0}
                  </div>
                  <div className="text-xs text-gray-600 uppercase tracking-wide">Groups Updated</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600 mb-1">
                    {Object.values(importResult?.skus_not_found || {}).reduce((acc: number, skus: any) => acc + skus.length, 0)}
                  </div>
                  <div className="text-xs text-gray-600 uppercase tracking-wide">SKUs Not Found</div>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="p-6 bg-gray-50 border-t border-gray-200">
              {/* Two Column Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pb-0">
                {/* Groups Updated */}
                <div>
                  <h3 className="font-semibold text-gray-700 uppercase text-xs tracking-wider mb-3">
                    GROUPS UPDATED
                  </h3>
                  <div className="bg-white rounded-lg border border-gray-300 overflow-hidden h-[300px]">
                    <div className="overflow-auto h-full">
                      <table className="w-full">
                        <thead className="bg-gray-100/80 sticky top-0 border-b border-gray-200">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">#</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Group Name</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                          {importResult?.groups_updated?.map((group: string, idx: number) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm text-gray-500">{idx + 1}</td>
                              <td className="px-4 py-3 text-sm text-gray-900">{group}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* SKUs Added by Group */}
                <div>
                  <h3 className="font-semibold text-gray-700 uppercase text-xs tracking-wider mb-3">
                    SKUS ADDED BY GROUP
                  </h3>
                  <div className="bg-white rounded-lg border border-gray-300 overflow-hidden h-[300px]">
                    <div className="overflow-auto h-full">
                      <table className="w-full">
                        <thead className="bg-gray-100/80 sticky top-0 border-b border-gray-200">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">#</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Group Name</th>
                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-600">Added</th>
                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-600">Existed</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                          {Object.entries(importResult?.skus_added || {}).map(
                            ([group, stats]: [string, any], idx: number) => (
                              <tr key={idx} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-sm text-gray-500">{idx + 1}</td>
                                <td className="px-4 py-3 text-sm text-gray-900">{group}</td>
                                <td className="px-4 py-3 text-sm text-center">
                                  <span className="text-emerald-600 font-semibold flex items-center justify-center gap-1">
                                    <CheckCircle className="w-4 h-4" />
                                    {stats.added}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-center font-semibold text-amber-600">
                                  {stats.already_exists}
                                </td>
                              </tr>
                            ),
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>

              {/* SKUs Not Found */}
              {Object.keys(importResult?.skus_not_found || {}).length > 0 && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-700 uppercase text-xs tracking-wider">
                      SKUS NOT FOUND ({Object.values(importResult?.skus_not_found || {}).reduce((acc: number, skus: any) => acc + skus.length, 0)})
                    </h3>
                    <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                      <button
                        onClick={handleExportNotFoundSkus}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 transition-colors border-r border-gray-300"
                      >
                        <Download className="w-4 h-4" />
                        <span className="font-medium">Export</span>
                      </button>
                      <button
                        onClick={toggleAllDetails}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                      >
                        <span className="font-medium">{allExpanded ? 'Collapse All' : 'Expand All'}</span>
                        <ChevronDown className={`w-4 h-4 text-gray-600 transition-transform ${allExpanded ? 'rotate-180' : ''}`} />
                      </button>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg border border-gray-300 overflow-hidden">
                    <div className="divide-y divide-gray-200">
                      {Object.entries(importResult?.skus_not_found || {}).map(
                        ([group, skus]: [string, any], idx: number) => (
                          <details
                            key={idx}
                            className="group bg-white"
                            ref={(el) => {
                              if (el) detailsRefs.current[idx] = el;
                            }}
                          >
                            <summary className="px-4 py-3 cursor-pointer hover:bg-red-50 flex items-center justify-between border-l-4 border-transparent hover:border-red-500">
                              <span className="text-sm font-medium text-red-700">{group}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-sm text-red-600 font-medium">{skus.length} SKUs</span>
                                <ChevronDown className="w-4 h-4 text-red-500 group-open:rotate-180 transition-transform" />
                              </div>
                            </summary>
                            <div className="px-6 py-4 bg-red-50/30 border-t border-red-100">
                              <div className="grid grid-cols-4 gap-3">
                                {skus.map((sku: string, skuIdx: number) => (
                                  <div key={skuIdx} className="text-sm font-mono text-gray-700 bg-white px-4 py-3 rounded border border-gray-200 text-center">{sku}</div>
                                ))}
                              </div>
                            </div>
                          </details>
                        ),
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Search Filter for Groups */}
        {!loading && groups.length > 0 && (
          <div className="bg-white rounded-lg shadow p-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search watchlist groups..."
                value={groupSearchTerm}
                onChange={(e) => setGroupSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {/* Groups Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600"></div>
          </div>
        ) : groups.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No SKU groups yet
            </h3>
            <p className="text-gray-500 mb-4">
              Create your first group to start tracking products
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
            >
              <Plus className="w-5 h-5" />
              Create Group
            </button>
          </div>
        ) : (
          (() => {
            const filteredGroups = groups.filter((group) =>
              group.name.toLowerCase().includes(groupSearchTerm.toLowerCase())
            );

            if (filteredGroups.length === 0) {
              return (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No groups found
                  </h3>
                  <p className="text-gray-500 mb-4">
                    No watchlist groups match "{groupSearchTerm}"
                  </p>
                  <button
                    onClick={() => setGroupSearchTerm("")}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
                  >
                    Clear Search
                  </button>
                </div>
              );
            }

            return (
              <div className="space-y-4">
                {filteredGroups.map((group) => (
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
                    <Button
                      variant="outline-success"
                      onClick={() => handleExportGroup(group)}
                      disabled={exportingGroupId === group.group_id || group.product_count === 0}
                      loading={exportingGroupId === group.group_id}
                      icon={<Download className="w-4 h-4" />}
                      title="Export SKUs to Excel"
                    >
                      {exportingGroupId === group.group_id ? "Exporting..." : "Export"}
                    </Button>

                    <Button
                      variant="outline-primary"
                      onClick={() => { setSelectedGroup(group); setShowAddProductModal(true); setSearchTerm(""); }}
                      icon={<Plus className="w-4 h-4" />}
                    >
                      Manage Products
                    </Button>

                    <button onClick={() => handleDeleteGroup(group.group_id)} className="p-2 hover:bg-red-50 rounded-lg transition-colors" title="Delete group">
                      <Trash2 className="w-5 h-5 text-red-600" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
            );
          })()
        )}

        {/* Create Group Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/10 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Create New SKU Group
              </h2>

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
                <Button variant="outline" className="flex-1" onClick={() => { setShowCreateModal(false); setNewGroupName(""); }}>Cancel</Button>
                <Button variant="primary" className="flex-1" onClick={handleCreateGroup}>Create Group</Button>
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
                    setSearchTerm("");
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
                              {product.price
                                ? `฿${product.price.toLocaleString()}`
                                : "-"}
                            </div>
                            <div className="flex-1 min-w-0 text-sm text-gray-900 truncate">
                              {product.name}
                            </div>
                            <button
                              onClick={() =>
                                handleRemoveProduct(
                                  selectedGroup.group_id,
                                  product.sku,
                                )
                              }
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
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Available Products
                  </h3>

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
                    <p className="text-gray-500 text-center py-8">
                      No products found
                    </p>
                  ) : (
                    <div className="space-y-1">
                      {filteredProducts
                        .filter(
                          (prod) =>
                            !selectedGroup.products.some(
                              (p) => p.sku === prod.sku,
                            ),
                        )
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
                              {product.price
                                ? `฿${product.price.toLocaleString()}`
                                : "-"}
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

        {/* Create Group Modal */}
      </div>
    </MainLayout>
  );
}
