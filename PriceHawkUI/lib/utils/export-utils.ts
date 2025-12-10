import Papa from 'papaparse';
import { ProductComparison, Retailer, RetailerNames } from '../types/price-comparison';
import { formatCurrency, getStatusLabel } from './price-utils';

/**
 * Export product data to CSV format
 * @param products - Array of product comparison data
 * @param filename - Optional custom filename (default: auto-generated with timestamp)
 * @returns void - Triggers browser download
 */
export function exportToCSV(
  products: ProductComparison[],
  filename?: string
): void {
  // Transform products into flat CSV format
  const csvData = products.map((product, index) => ({
    'No.': index + 1,
    'Category': product.categoryTh || product.category,
    'SKU': product.sku,
    'Product Name': product.nameTh || product.name,
    'Brand': product.brand,
    'Thai Watsadu': formatCurrency(product.prices[Retailer.THAI_WATSADU].price, false),
    'Thai Watsadu URL': product.prices[Retailer.THAI_WATSADU].productUrl || '',
    'HomePro': formatCurrency(product.prices[Retailer.HOMEPRO].price, false),
    'HomePro URL': product.prices[Retailer.HOMEPRO].productUrl || '',
    'Global House': formatCurrency(product.prices[Retailer.GLOBAL_HOUSE].price, false),
    'Global House URL': product.prices[Retailer.GLOBAL_HOUSE].productUrl || '',
    'DoHome': formatCurrency(product.prices[Retailer.DOHOME].price, false),
    'DoHome URL': product.prices[Retailer.DOHOME].productUrl || '',
    'Boonthavorn': formatCurrency(product.prices[Retailer.BOONTHAVORN].price, false),
    'Boonthavorn URL': product.prices[Retailer.BOONTHAVORN].productUrl || '',
    'Status': getStatusLabel(product.status),
    'Lowest Price': formatCurrency(product.lowestPrice, false),
    'Highest Price': formatCurrency(product.highestPrice, false),
    'Price Difference %': product.priceDifferencePercent?.toFixed(2) || '',
  }));

  // Convert to CSV using papaparse
  const csv = Papa.unparse(csvData, {
    quotes: true,
    delimiter: ',',
    header: true,
  });

  // Generate filename if not provided
  const finalFilename = filename || generateFilename('price-comparison', 'csv');

  // Trigger download
  downloadFile(csv, finalFilename, 'text/csv;charset=utf-8;');
}

/**
 * Generate filename with timestamp
 * @param prefix - Filename prefix
 * @param extension - File extension (without dot)
 * @returns Formatted filename
 */
export function generateFilename(prefix: string, extension: string): string {
  const now = new Date();
  const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, -5);
  return `${prefix}_${timestamp}.${extension}`;
}

/**
 * Trigger browser download of a file
 * @param content - File content
 * @param filename - Filename
 * @param mimeType - MIME type
 */
function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const link = document.createElement('a');

  if (link.download !== undefined) {
    // Create a link to the file
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up the URL object
    setTimeout(() => URL.revokeObjectURL(url), 100);
  }
}

/**
 * Export filtered products only
 * @param allProducts - All available products
 * @param filterFn - Filter function to apply
 * @param filename - Optional custom filename
 */
export function exportFilteredProducts(
  allProducts: ProductComparison[],
  filterFn: (product: ProductComparison) => boolean,
  filename?: string
): void {
  const filteredProducts = allProducts.filter(filterFn);
  exportToCSV(filteredProducts, filename);
}
