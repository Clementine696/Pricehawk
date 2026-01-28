import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Upload, Plus, X, FileSpreadsheet, CheckCircle2 } from 'lucide-react';
import ImportSummaryStats from '@/components/watchlist/ImportSummaryStats';
import GroupsUpdatedTable from '@/components/watchlist/GroupsUpdatedTable';
import SKUsAddedTable from '@/components/watchlist/SKUsAddedTable';
import SKUsNotFoundTable from '@/components/watchlist/SKUsNotFoundTable';
import SKUGroupCard from '@/components/watchlist/SKUGroupCard';

interface SKUGroup {
  id: string;
  name: string;
  productCount: number;
}

interface ImportResult {
  totalRows: number;
  groupsProcessed: number;
  groupsUpdated: string[];
  skusAddedByGroup: { name: string; added: number; existed: number }[];
  skusNotFound: { group: string; skus: string[] }[];
}

const mockGroups: SKUGroup[] = [
  { id: '1', name: '101_Sheet / Board', productCount: 35 },
  { id: '2', name: '109_Material', productCount: 0 },
  { id: '3', name: '111_Block', productCount: 0 },
  { id: '4', name: '306_Ceramics Wall Tiles & Glass Block & Marble/ Granite/ Stone', productCount: 0 },
  { id: '5', name: '113_Steel Material', productCount: 0 },
  { id: '6', name: '104_Chemical & Safety & Furniture Fitting & Stationery', productCount: 69 },
];

const mockImportResult: ImportResult = {
  totalRows: 5475,
  groupsProcessed: 51,
  groupsUpdated: [
    '101_Sheet / Board',
    '102_Architectural Wood',
    '102_Door / Frame & Sliding Door/Window & Window',
    '104_Carpet / Net & Accessories & Metal Gate & Fence Accessories',
    '104_Chemical & Safety & Furniture Fitting & Stationery',
    '105_Door Hardware',
    '106_Hand Tools',
    '106_Power Tool Accessories',
    '106_Powertools',
    '107_Automotive',
    '108_Roofing',
    '109_Material',
    '110_Insulation & Frame',
    '111_Block',
    '112_Building Equipment',
    '113_Steel Material',
    '114_Pipe',
    '201_Ceiling Lamp & Ceiling Lamp & Fanlamp & Wall Light',
  ],
  skusAddedByGroup: [
    { name: '101_Sheet / Board', added: 12, existed: 23 },
    { name: '102_Architectural Wood', added: 0, existed: 6 },
    { name: '102_Door / Frame & Sliding Door/Window & Window', added: 5, existed: 33 },
    { name: '104_Chemical & Safety & Furniture Fitting & Stationery', added: 3, existed: 69 },
    { name: '105_Door Hardware', added: 0, existed: 27 },
    { name: '106_Hand Tools', added: 8, existed: 49 },
  ],
  skusNotFound: [
    {
      group: '101_Sheet / Board',
      skus: ['60289950', '60132097', '60212003', '60343218', '60319509', '60359081', '60132138', '60269962', '60255078', '60136574'],
    },
    {
      group: '102_Architectural Wood',
      skus: ['60322228', '60311780', '60420640'],
    },
  ],
};

const WatchlistSKU = () => {
  const [groups] = useState<SKUGroup[]>(mockGroups);
  const [showImportResults, setShowImportResults] = useState(false);
  const [importResult] = useState<ImportResult>(mockImportResult);

  const handleImportExcel = () => {
    setShowImportResults(true);
  };

  const handleCreateGroup = () => {
    alert('Create new group...');
  };

  const handleExport = (groupId: string) => {
    alert(`Exporting group ${groupId}...`);
  };

  const handleManageProducts = (groupId: string) => {
    alert(`Managing products for group ${groupId}...`);
  };

  const handleDelete = (groupId: string) => {
    alert(`Deleting group ${groupId}...`);
  };

  const handleExportNotFoundCSV = () => {
    alert('Exporting CSV...');
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Watchlist SKU</h1>
          <p className="text-muted-foreground mt-1">จัดการ SKU groups และติดตามราคาสินค้า</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleImportExcel}>
            <Upload className="h-4 w-4 mr-2" />
            Import Excel
          </Button>
          <Button onClick={handleCreateGroup}>
            <Plus className="h-4 w-4 mr-2" />
            Create Group
          </Button>
        </div>
      </div>

      {/* Import Results Section */}
      {showImportResults && (
        <div className="bg-card border rounded-2xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b bg-muted/30">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <h2 className="font-semibold text-foreground">Import Completed</h2>
                <p className="text-sm text-muted-foreground">ไฟล์ถูกประมวลผลเรียบร้อยแล้ว</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowImportResults(false)}
              className="text-muted-foreground"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Summary Stats */}
          <div className="p-6 border-b">
            <ImportSummaryStats
              totalRows={importResult.totalRows}
              groupsProcessed={importResult.groupsProcessed}
              groupsUpdated={importResult.groupsUpdated.length}
              skusNotFound={importResult.skusNotFound.reduce((acc, g) => acc + g.skus.length, 0)}
            />
          </div>

          {/* Tables Grid - Top Row */}
          <div className="p-6 pb-0">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <GroupsUpdatedTable groups={importResult.groupsUpdated} />
              <SKUsAddedTable items={importResult.skusAddedByGroup} />
            </div>
          </div>

          {/* SKUs Not Found - Full Width */}
          <div className="p-6">
            <SKUsNotFoundTable groups={importResult.skusNotFound} />
          </div>
        </div>
      )}

      {/* Groups Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">
            Your Groups
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({groups.length})
            </span>
          </h2>
        </div>

        <div className="space-y-3">
          {groups.map((group) => (
            <SKUGroupCard
              key={group.id}
              group={group}
              onExport={handleExport}
              onManage={handleManageProducts}
              onDelete={handleDelete}
            />
          ))}
        </div>

        {groups.length === 0 && (
          <div className="text-center py-16 text-muted-foreground">
            <FileSpreadsheet className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="font-medium">ยังไม่มี SKU Groups</p>
            <p className="text-sm mt-1">สร้าง group ใหม่หรือ import จาก Excel</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default WatchlistSKU;
