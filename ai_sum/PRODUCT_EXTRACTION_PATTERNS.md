# Product Extraction Patterns - All Retailers

**Last Updated**: 2026-03-05  
**Location**: `backend/scraper-url/adws/adw_modules/product_extractor.py`  
**Purpose**: Comprehensive documentation of all extraction patterns for 6 retailers

---

## Table of Contents
1. [Thai Watsadu](#1-thai-watsadu)
2. [HomePro](#2-homepro)
3. [Boonthavorn](#3-boonthavorn)
4. [MegaHome](#4-megahome)
5. [DoHome](#5-dohome)
6. [Global House](#6-global-house)
7. [Common Patterns](#common-patterns)

---

## 1. THAI WATSADU

**Retailer ID**: `twd`  
**Website**: thaiwatsadu.com  
**Technology**: Next.js / React

### Price Extraction (Priority Order)

#### PRIMARY: HTML DOM (Most Reliable)

**Case 1: Pack/Multiple Pricing - "1 ชิ้น" (1 piece) price**
```regex
<div[^>]*class="[^"]*whitespace-nowrap[^"]*font-semibold[^"]*"[^>]*>
  1\s*(?:<!--|&nbsp;|<!--\s*-->)\s*ชิ้น
</div>
(?:(?!</div>).)*?
<div[^>]*class="[^"]*text-primary[^"]*text-\[(?:24|40)px\][^"]*font-price[^"]*"[^>]*>
  ([\d,]+(?:\.\d+)?)
</div>
```
- Matches large text (40px) for single unit or 24px for pack
- Anchors on "1 ชิ้น" label

**Case 2 & 3: Discount/Coupon Price (Red text)**
```regex
<span[^>]*class="[^"]*text-redPrice[^"]*"[^>]*>฿</span>
\s*
<span[^>]*class="[^"]*font-price[^"]*text-redPrice[^"]*"[^>]*>
  ([\d,]+(?:\.\d+)?)
</span>
```
- **Key Class**: `text-redPrice` + `font-price`
- Anchors on `฿` symbol in preceding span
- Supports decimals: `[\d,]+(?:\.\d+)?`

**Original Price (line-through)**
```regex
<div[^>]*class="[^"]*text-grayDark[^"]*line-through[^"]*"[^>]*>
  ราคาเดิม(?:<!--|&nbsp;|<!--\s*-->|\s)*(?:<!--|&nbsp;|<!--\s*-->|\s)*
  ([\d,]+(?:\.\d{2})?)
</div>
```
- **Key Classes**: `text-grayDark` + `line-through`
- Contains "ราคาเดิม" (original price) text

**Additional Discount Badge**
```regex
ซื้อตอนนี้ลดเพิ่ม\s*([\d,]+)
```
- Detects "Buy now get extra discount" badge
- Subtracts discount amount from current price

#### SECONDARY: JSON Data

**__NEXT_DATA__ JSON**
```regex
<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>
```
**Individual Price**:
```regex
"price"\s*:\s*"(\d+)"[^}]*"prUname"\s*:\s*"EACH
```
**Discount Price**:
```regex
"disc"\s*:\s*"([\d.]+)"
```

**JSON-LD**
```javascript
offers.price  // From JSON-LD schema
```

---

### SKU Extraction

**URL Pattern (Most Reliable)**
```regex
Pattern 1: -(\d{8})(?:\?|$)     // Example: /product/name-60272160
Pattern 2: /sku/(\d+)            // Example: /th/sku/60272160
```
- Always 8 digits for Thai Watsadu
- JSON-LD SKU often contaminated - NOT used

---

### Brand Extraction

**Priority Order**:

1. **HTML Brand Link** (Most Reliable)
```regex
href="/th/brand/([^"]+)"[^>]*>([^<]+)</a>
```
- Use `group(2)` for text content (not href to avoid URL encoding)

2. **Product Name Pattern**
```regex
([A-Z][A-Z0-9]+)\s+รุ่น
```
- Example: "MAKITA รุ่น ABC" → Brand: "MAKITA"

3. **JSON-LD**
```javascript
brand.name
```

---

### Category Extraction

**Priority Order**:

1. **categoryBar Pattern** (Most Reliable)
```regex
<a[^>]*class="[^"]*categoryBar_journeyNavText[^"]*"[^>]*>([^<]+)</a>
```
- Returns **last match** (most specific category)

2. **JSON-LD BreadcrumbList**
```javascript
@type: "BreadcrumbList"
itemListElement[].name
```
- Skip: `['หน้าแรก', 'home', 'สินค้า', 'products', 'ทั้งหมด', 'all', 'thaiwatsadu', 'ไทวัสดุ']`

3. **Standard Breadcrumb HTML**
```regex
<nav[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</nav>
```

---

### Image Extraction

**Next.js Image Format**

1. **srcset Attributes** (Primary)
```regex
srcset="([^"]*/_next/image\?url=https%3A%2F%2Fpim\.thaiwatsadu\.com[^"]*)"
```
- Extract URLs from srcset (supports multiple resolutions)
- URL-decode: `https%3A%2F%2F` → `https://`
- Filter: Exclude `/badge/` images

2. **SKU-Specific Images**
```regex
src="(/_next/image\?url=[^"]*{sku}[^"]*)"
```

3. **Direct PIM URLs**
```regex
src="(https://pim\.thaiwatsadu\.com[^"]+)"
```

**Limit**: 10 images max

---

### Specifications Extraction

**Custom Section**: "ข้อมูลเฉพาะสินค้า" (Product Information)

**Flex-based Table Pairs**:
```regex
<div>{LABEL}</div></div><div class="w-1/2"><div>([^<]+)</div>
```

**Label Mapping**:
- `ขนาด (กxลxส)(ซม.)` → dimensions
- `วัสดุหลัก` → material
- `แบรนด์` / `ยี่ห้อ` → brand
- `สี` → color
- `รุ่น` → model
- `น้ำหนัก (กก.)` → weight

**Dimensions Pattern**:
```regex
<div>(\d+\s*x\s*\d+\s*x\s*\d+)</div>
```

**Delivery Size Format**:
```regex
\((?:<!--[^>]*-->)*ก(?:<!--[^>]*-->)*\)(?:<!--[^>]*-->)*([\d.]+)(?:<!--[^>]*-->)*
\s*x\s*
\((?:<!--[^>]*-->)*ย(?:<!--[^>]*-->)*\)(?:<!--[^>]*-->)*([\d.]+)(?:<!--[^>]*-->)*
\s*x\s*
\((?:<!--[^>]*-->)*ส(?:<!--[^>]*-->)*\)(?:<!--[^>]*-->)*([\d.]+)
```
- Format: `(ก)35 x (ย)67 x (ส)50` (Width x Depth x Height)

**Color from Name**:
```regex
สี([ก-๙a-zA-Z]+)
```

**Model from Name**:
```regex
รุ่น\s+([A-Za-z0-9\-_.]+)
```

---

### Special Features

- **Text Cleaning**: Removes Thai Watsadu branding
  - Filter: `['ไทวัสดุ', 'thaiwatsadu', 'ครบเรื่องบ้าน ถูกและดี']`
- **Decimal Support**: All price patterns support `.XX` decimals
- **Badge Detection**: Additional discounts extracted and applied
- **Next.js Wrapper**: Handles `/_next/image?url=...` format

---

## 2. HOMEPRO

**Retailer ID**: `hp`  
**Website**: homepro.co.th  
**Technology**: Traditional server-side rendering

### Price Extraction (Priority Order)

#### PRIMARY: SKU-Anchored Inputs (Most Reliable)

**1. Net Price (Online Discount)**
```regex
gtmIsNetPrice-{SKU}[^>]*value=["\']true["\']
# If true, extract:
<input[^>]*id=["\']gtmNetPrice-{SKU}["\'][^>]*value=["\']([\d.]+)["\']
```
- **Key**: Anchored to specific SKU
- Highest priority when `gtmIsNetPrice=true`

**2. GTM Price Hidden Input**
```regex
<input[^>]*id=["\']gtmPrice-{SKU}["\'][^>]*value=["\']([\d.]+)["\']
```
- **Key**: `id="gtmPrice-{SKU}"`
- Direct price value, no parsing needed

**3. JavaScript Analytics (Facebook Pixel/GTM)**
```regex
id\s*:\s*["\']?{SKU}["\']?.{0,300}?item_price\s*:\s*["\'](\d+)["\']
```
- Searches within 300 chars of SKU in analytics data

#### SECONDARY: HTML Fallback

**1. Discount Price Container**
```regex
<div[^>]*class="[^"]*discount-price[^"]*"[^>]*>.*?
<span[^>]*class="[^"]*amount[^"]*"[^>]*>([\d,]+)</span>
```
- **Key Class**: `discount-price` container + `amount` span

**2. OBCon Price Info**
```regex
obcon-price-info[^>]*>.*?
<span[^>]*class="[^"]*amount[^"]*"[^>]*>([\d,]+)</span>
```

**3. Price Div with ฿**
```regex
<div[^>]*class="[^"]*price[^"]*"[^>]*>\s*(?:<[^>]*>)*\s*฿\s*([\d,]+)</div>
```

**4. Meta Tag**
```regex
<meta[^>]*property=["\']product:price:amount["\'][^>]*content=["\']([\d.]+)["\']
```

**Original Price**:
```regex
<div[^>]*class=["\']original-price["\'][^>]*>.*?
<span[^>]*class=["\']amount["\'][^>]*>([\d,]+)</span>
```
```regex
<span[^>]*class="[^"]*line-through[^"]*"[^>]*>.*?฿?\s*([\d,]+)
```

---

### SKU Extraction

**URL Pattern**
```regex
/p/(\d+)
```
- Example: `/p/246513`

---

### Brand Extraction

**Priority Order**:

1. **JSON-LD**
```javascript
brand.name
```

2. **Known Brands List**
```python
known_brands = [
    'HG', 'KARCHER', 'BOSCH', 'MAKITA', 'DEWALT', 'MILWAUKEE', 'STANLEY',
    'BLACK+DECKER', 'PHILIPS', 'PANASONIC', 'TOSHIBA', 'LG', 'SAMSUNG',
    'ELECTROLUX', 'MITSUBISHI', 'DAIKIN', 'HITACHI', 'SHARP', 'HAIER',
    'TOA', 'BEGER', 'NIPPON', 'JOTUN', 'DULUX',
    'COTTO', 'AMERICAN STANDARD', 'KOHLER', 'GROHE', 'TOTO',
    'YALE', 'HAFELE', 'SCHLAGE', 'SCG', '3M', 'SCOTCH-BRITE'
]
```
- Case-insensitive check

3. **Uppercase Word from Name**
```regex
\b([A-Z][A-Z0-9+\-]{1,15})\b
```
- Matches 2-16 char uppercase words

---

### Category Extraction

**Breadcrumb Navigation**
```regex
<nav[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</nav>
```
- Skip: `['หน้าแรก', 'home', 'homepro', 'โฮมโปร', 'สินค้า', 'products']`

---

### Image Extraction

**HomePro CDN Pattern**
```regex
<img[^>]*src="(https://(?:cdn|ecatalog-media)\.homepro\.co\.th/[^"]*ART_IMAGE[^"]+)"
```
```regex
"(https://(?:cdn|ecatalog-media)\.homepro\.co\.th/[^"]*ART_IMAGE[^"]+)"
```
- **Must contain**: `ART_IMAGE`
- **Domains**: `cdn.homepro.co.th` or `ecatalog-media.homepro.co.th`

---

### Specifications Extraction

**Table-Based**:
- Extract from `<table>` elements with specification rows
- Dimensions: Built from width × depth × height

**Invalid Model Filter**:
```python
['อื่น', 'อื่นๆ', 'other', 'others', '-', 'n/a', 'na', 'none']
```

---

### Special Features

- **Debug Logging**: Saves HTML to `results/debug_homepro_{sku}.html`
- **CSS Color Prevention**: Filters out color codes from text fields
- **SKU-Anchored Extraction**: Most reliable method across all retailers
- **Analytics Integration**: Extracts from Facebook Pixel and GTM data

---

## 3. BOONTHAVORN

**Retailer ID**: `btv`  
**Website**: boonthavorn.com  
**Technology**: React-based

### Price Extraction

#### PRIMARY: JSON-LD
```javascript
offers.price
```
- Most reliable for Boonthavorn

#### Original Price
```regex
productPrice-oldPrice.*?price-currency-[^>]+>บาท</span>
((?:<span>[^<]+</span>)+)
```
- Clean: Remove tags `<[^>]+>` and commas

---

### SKU Extraction

**Priority Order**:

1. **JSON-LD**
```javascript
sku
```

2. **Quick Info Section**
```regex
class="quickInfo-infoLabel-[^"]+">รหัสสินค้า</label>
<label class="quickInfo-infoValue-[^"]+">([^<]+)</label>
```
- **Key Classes**: `quickInfo-infoLabel` + `quickInfo-infoValue`

3. **URL Fallback**
```regex
-(\d+)$
```

---

### Brand Extraction

**Priority Order**:

1. **JSON-LD**
```javascript
brand.name
```

2. **Quick Info Section**
```regex
class="quickInfo-infoLabel-[^"]+">ยี่ห้อ</label>
<label class="quickInfo-infoValue-[^"]+">([^<]+)</label>
```

---

### Category Extraction

**Breadcrumbs**
```regex
<a[^>]*class="breadcrumbs-link-[^"]*"[^>]*>([^<]+)</a>
```
- **Take last link** (most specific category before product)
- **Key Class**: `breadcrumbs-link-*` (dynamic hash)

---

### Image Extraction

**JSON-LD Primary**
```javascript
image  // Can be string or array
```

---

### Specifications Extraction

**Quick Info Pattern**:
```regex
<label[^>]*class="quickInfo-infoLabel[^"]*">{LABEL}</label>
<label[^>]*class="quickInfo-infoValue[^"]*">([^<]+)</label>
```

**Fields**:
- `สี` → color
- `ขนาดสินค้า` → dimensions
- `น้ำหนัก` → weight/volume

**Alternative Weight Patterns**:
```regex
productAttributes-name[^>]*>น้ำหนัก</span>.*?
richContent-root[^>]*>([^<]+)</div>
```
```regex
น้ำหนัก[:\s]*([0-9.]+\s*(?:KG|kg|Kg|กก\.|กิโลกรัม))
```

**Model from Name**:
```regex
รุ่น\s+([A-Za-z0-9\-_\s]+)
```

---

### Special Features

- **QuickInfo System**: Label-value pairs for all specs
- **Dynamic Classes**: Uses hash suffixes (e.g., `quickInfo-infoLabel-mHX`)
- **Weight Extraction**: Multiple fallback patterns
- **JSON-LD Primary**: Most reliable source for basic data

---

## 4. MEGAHOME

**Retailer ID**: `mgh`  
**Website**: megahome.co.th  
**Technology**: Similar to HomePro platform

### Price Extraction (Priority Order)

#### PRIMARY: HTML DOM

**1. Normal Discount Price**
```regex
<div class="discount-price">.*?
<span class="amount">([0-9,.]+)</span>
```
- **Key Class**: `discount-price` + `amount`

**2A. Swiper Carousel "1 ea" Slide**
```regex
onclick="setItemScaling\((?:\'|&#39;)1(?:\'|&#39;)\);".*?
<span class="amount">([0-9,.]+)</span>
```
- Extracts single unit price from bulk pricing carousel
- **Key**: `onclick="setItemScaling('1')"`

**2B. Scale Price Range**
```regex
<span class="scale-price">(.*?)</span>\s*</div>
```
Then extract all:
```regex
<span class="amount">([0-9,.]+)</span>
```
- **Take LAST amount** = single unit = highest price

**Fallback: Hidden GTM Input**
```regex
<input[^>]*id="gtmPrice-\d+"[^>]*value="([0-9.]+)"
```

#### Original Price
```regex
<div class="original-price">.*?
<span class="amount">([0-9,.]+)</span>
```

---

### SKU Extraction

**URL Pattern**
```regex
/p/(\d+)
```

---

### Brand Extraction

**prd-brand Div**
```regex
<div class="prd-brand">\s*<a[^>]*>([^<]+)</a>
```
- **Key Class**: `prd-brand`

---

### Category Extraction

**Breadcrumb Section Links**
```regex
<a class="section"[^>]*>([^<]+)</a>
```
- **Take last match**
- **Key Class**: `section`

---

### Image Extraction

**Image Index Elements**
```regex
<img[^>]*id="image-index-\d+"[^>]*src="([^"]+)"
```
- **Key ID Pattern**: `image-index-{number}`

---

### Specifications Extraction

**Product Name**:
```regex
<div class="prd-name">\s*<h1>([^<]+)</h1>
```

**Table with Category Prefixes**:
```regex
class="pdp-[A-Z]+_{FIELD}"[^>]*>.*?
<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>
```

**Fields**:
- `pdp-*_MATERIAL` → material
- `pdp-*_COLOR` → color
- `pdp-*_WIDTH` → width
- `pdp-*_DEPTH` → depth
- `pdp-*_HEIGHT` → height
- `pdp-*_WEIGHT` → weight

**Dimensions Built As**:
```
{width} x {depth} x {height} cm
```

**Color from Name**:
```regex
สี(\S+)
```

**Model from Name**:
```regex
(?:NO\.|รุ่น\s*)([A-Za-z0-9\-_.]+)
```

---

### Special Features

- **Bulk Pricing**: Handles multi-unit pricing with scale ranges
- **Swiper Carousel**: Extracts single unit from pricing carousel
- **Category Prefixes**: Dynamic `pdp-{CATEGORY}_` pattern for specs
- **Last Price Logic**: Takes highest (single unit) price from range

---

## 5. DOHOME

**Retailer ID**: `dh`  
**Website**: dohome.co.th  
**Technology**: Next.js / Modern stack

### Price Extraction (Priority Order)

#### PRIMARY: HTML DOM

**1. Main Price (text-3xl font-semibold)**
```regex
<span[^>]*class="[^"]*text-3xl[^"]*font-semibold[^"]*"[^>]*>
฿?([\d,]+(?:\.\d{2})?)
</span>
```
- **Key Classes**: `text-3xl` + `font-semibold`
- Supports decimals

**2. JSON Market Price**
```regex
"marketPrice"\s*:\s*"฿?([\d,]+(?:\.\d{2})?)"
```

**3. JSON Sale Price**
```regex
"salePrice"\s*:\s*"฿?([\d,]+(?:\.\d{2})?)"
```

**4. Generic Price with ฿**
```regex
>฿([\d,]+(?:\.\d{2})?)<
```

#### Original Price

**`<s>` Strikethrough Tag** (2024 pattern)
```regex
<s[^>]*>฿?([\d,]+(?:\.\d{2})?)</s>
```

**Old Price Patterns**:
```regex
<span[^>]*class="[^"]*old-price[^"]*"[^>]*>(.*?)</span>
```
```regex
ราคาปกติ[:\s]*([฿]?[\d,]+\.?\d*)
```

---

### SKU Extraction

**Priority Order**:

1. **JSON-LD**
```javascript
sku
```

2. **URL Pattern**
```regex
-(\d{6,})(?:\?|$)
```
- Example: `/product/name-10026550`
- 6+ digits

---

### Brand Extraction

**Priority Order**:

1. **JSON-LD**
```javascript
brand.name
```

2. **Brand Link**
```regex
<a[^>]*href="/brand/[^"]*"[^>]*>([^<]+)</a>
```

3. **Brand Span**
```regex
<span[^>]*class="[^"]*brand[^"]*"[^>]*>([^<]+)</span>
```

---

### Category Extraction

**Priority Order**:

1. **Category Link**
```regex
<a[^>]*href="/category/[^"]*"[^>]*>([^<]+)</a>
```

2. **JSON categoryName**
```regex
"categoryName"\s*:\s*"([^"]+)"
```

**Skip**: `['หน้าแรก', 'home', 'สินค้า', 'products', 'dohome']`

---

### Image Extraction

Uses **base class extraction** (standard patterns)

---

### Specifications Extraction

**Next.js JSON with Escaped Quotes**:

**Dimension Object**:
```regex
\\?"dimension\\?"\s*:\s*\{
  [^}]*\\?"width\\?"\s*:\s*([\d.]+)
  [^}]*\\?"long\\?"\s*:\s*([\d.]+)
  [^}]*\\?"high\\?"\s*:\s*([\d.]+)
  [^}]*\\?"weight\\?"\s*:\s*([\d.]+)
\}
```
- **Note**: Escaped quotes `\"` in Next.js script tags

**Dimensions Built As**:
```
{width} x {length} x {height} cm
```

**Weight**: Stored in `volume` field

**Model Extraction**:
```regex
\\?"productModel\\?"\s*:\s*\\?"([^"\\]+)\\?"
```

---

### Special Features

- **Escaped JSON**: Handles `\"` in Next.js script tags
- **Decimal Support**: All patterns support `.XX` decimals
- **Strikethrough Tag**: Modern `<s>` tag for original price
- **Dimension Object**: Complete W×L×H×Weight in one JSON object

---

## 6. GLOBAL HOUSE

**Retailer ID**: `gbh`  
**Website**: globalhouse.co.th  
**Technology**: Next.js / Modern React

### Price Extraction (Priority Order)

#### PRIMARY: HTML DOM

**1. Sale Price in Red text-3xl**
```regex
<span[^>]*class="[^"]*text-3xl[^"]*text-red[^"]*"[^>]*>
฿?([\d,]+(?:\.\d+)?)
</span>
```
```regex
<span[^>]*class="[^"]*text-red[^"]*text-3xl[^"]*"[^>]*>
฿?([\d,]+(?:\.\d+)?)
</span>
```
- **Key Classes**: `text-3xl` + `text-red` (either order)
- **Supports decimals**: `(?:\.\d+)?`

**2. Font-bold Price**
```regex
<span[^>]*class="[^"]*font-bold[^"]*text-3xl[^"]*"[^>]*>
฿?([\d,]+(?:\.\d+)?)
</span>
```
- **Key Classes**: `font-bold` + `text-3xl`

**3. Generic Large Price**
```regex
<span[^>]*class="[^"]*text-(?:2|3)xl[^"]*"[^>]*>
฿?([\d,]+(?:\.\d+)?)
</span>
```
- Matches `text-2xl` or `text-3xl`

**Fallback: JSON-LD**
```javascript
offers.price
```

#### Original Price

**ราคาเดิม with line-through**
```regex
ราคาเดิม</span>\s*
<span[^>]*class="[^"]*line-through[^"]*"[^>]*>
฿?([\d,]+)
</span>
```

**Thai Word Pattern**
```regex
ราคาเดิม.*?฿([\d,]+)
```

**Legacy Patterns**
```regex
<span[^>]*class="[^"]*price[^"]*original[^"]*"[^>]*>(.*?)</span>
```

---

### SKU Extraction

**Priority Order**:

1. **URL Pattern** (Most Reliable)
```regex
-i\.(\d+)(?:\?|$)
```
- Example: `/product/MAZUMA-...-i.8852163012022`
- **Key**: `-i.{SKU}` format

2. **HTML Display**
```regex
รหัสสินค้า\s*:\s*(\d+)
```
- Format: `<div class="text-xs text-gray-400">รหัสสินค้า : 8852163012022</div>`

---

### Brand Extraction

**Priority Order**:

1. **JSON-LD**
```javascript
brand.name
```

2. **Header Brand Pattern**
```regex
สินค้าแบรนด์[^<]*</span>\s*<a[^>]*>([^<]+)</a>
```

3. **URL Extraction** (first word)
```regex
/product/([A-Za-z0-9]+)-
```

---

### Category Extraction

**Breadcrumb data-slot**
```regex
<a[^>]*data-slot="breadcrumb-link"[^>]*title="([^"]+)"
```
- **Key Attribute**: `data-slot="breadcrumb-link"`
- **Take last match**
- **Skip**: `['หน้าแรก', 'หมวดหมู่', 'สินค้า']`

---

### Image Extraction

**CDN Pattern**
```regex
https://www\.image-gbh\.com/uploads/[^"&\s]+\.(?:jpg|jpeg|png)
```
- **Domain**: `www.image-gbh.com`
- **Remove duplicates**, limit 10

---

### Specifications Extraction

**__NEXT_DATA__ Extraction**:
```regex
__NEXT_DATA__[^>]*type="application/json">(.+?)</script>
```

**Access Path**:
```javascript
next_data.props.pageProps.ast.data
ast_data.attributes[]  // Array of title/detail pairs
```

**Table-Cell Spec Pairs**:
```regex
data-slot="table-cell"[^>]*>([^<]+)</td>\s*
<td[^>]*data-slot="table-cell"[^>]*>(.*?)</td>
```
- **Key Attribute**: `data-slot="table-cell"`

**Fields**:
- `รุ่น` → model
- `แบรนด์` → brand
- `กว้าง` → width
- `ยาว` → length
- `สูง` → height

**Description from htmlContent**:
```javascript
ast_data.htmlContent[]  // Array with title='คุณสมบัติเด่น'
```

**Color from Name**:
```regex
สี(\S+)
```

---

### Special Features

- **Data-slot Attributes**: Modern attribute-based extraction
- **__NEXT_DATA__**: Complete product data in JSON
- **AST Structure**: Hierarchical data in `props.pageProps.ast.data`
- **Decimal Support**: All price patterns support `.XX` decimals
- **Dynamic Specs**: JavaScript-loaded specifications

---

## COMMON PATTERNS

### Base Price Patterns (All Retailers)

```regex
<span[^>]*class="[^"]*price[^"]*"[^>]*>(.*?)</span>
ราคา[:\s]*([฿$]?[\d,]+\.?\d*)
([฿$]?[\d,]+\.?\d*)\s*บาท
<meta[^>]*property=["\']product:price:amount["\'][^>]*content=["\']([^"\']+)["\']
```

---

### JSON-LD Structured Data

**All retailers support**:
```html
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "...",
  "sku": "...",
  "brand": { "name": "..." },
  "offers": {
    "price": "...",
    "priceCurrency": "THB"
  },
  "image": "..." or ["..."]
}
</script>
```

---

### Price Parsing

**PriceParser.parse_price()** handles:
- Comma separators: `1,234.56` → `1234.56`
- Thai Baht symbol: `฿1234` → `1234`
- Whitespace and HTML cleanup
- Decimal support: `[\d,]+(?:\.\d+)?`

---

### Sanitization Methods

**Applied to all extracted data**:

1. **_sanitize_brand_field()**
   - Removes HTML/CSS contamination
   - Filters CSS color codes
   - Max 50 chars

2. **_sanitize_sku_field()**
   - Validates SKU format
   - Prevents URLs
   - Prevents HTML tags
   - Max 50 chars

3. **_sanitize_color_field()**
   - Removes CSS color codes: `#[0-9A-Fa-f]{3,6}`
   - Prevents RGB values
   - Max 50 chars

4. **_sanitize_dimensions_field()**
   - Extracts dimension patterns
   - Format: `{number} x {number} x {number}`
   - Max 100 chars

5. **_sanitize_material_field()**
   - Filters company names
   - Removes URLs
   - Max 100 chars

6. **_sanitize_text_field()**
   - General text cleanup
   - Configurable max length
   - HTML tag removal

7. **_clean_text()**
   - Removes HTML tags and entities
   - Normalizes whitespace
   - Strips dangerous chars

---

### Invalid Value Filters

**Model**:
```python
['อื่น', 'อื่นๆ', 'other', 'others', '-', 'n/a', 'na', 'none']
```

**Material**:
```python
['ครบเรื่องบ้าน', 'ถูกและดี', 'บริษัท', 'จำกัด', 'corporation', 
 'http', 'www', '.com', '.co.th']
```

**Category Skip**:
```python
['หน้าแรก', 'home', 'สินค้า', 'products', 'ทั้งหมด', 'all']
```

---

## EXTRACTION HIERARCHY

### Priority Order (Most Retailers)

1. **Retailer-Specific HTML** (Highest Priority)
   - Custom class patterns
   - SKU-anchored elements
   - Data attributes

2. **JSON-LD Structured Data**
   - Standard schema.org format
   - Reliable but sometimes incomplete

3. **__NEXT_DATA__ / Analytics**
   - Next.js page props
   - GTM/Facebook Pixel data

4. **Generic HTML Patterns**
   - Fallback regex patterns
   - Meta tags

5. **Base Extractor** (Last Resort)
   - Common patterns across all sites
   - Lowest specificity

---

## DECIMAL PRICE SUPPORT

### Pattern Evolution

**Old Pattern** (No decimals):
```regex
[\d,]+
```

**Current Pattern** (With decimals):
```regex
[\d,]+(?:\.\d+)?
```
- Matches: `123`, `1,234`, `123.45`, `1,234.56`
- Optional decimal part: `(?:\.\d+)?`

### Affected Retailers

- ✅ **Thai Watsadu**: Full support (all 8 patterns)
- ✅ **Global House**: Full support (all 8 patterns)
- ✅ **DoHome**: Full support
- ⚠️ **HomePro**: Integer prices only
- ⚠️ **Boonthavorn**: Integer prices only
- ⚠️ **MegaHome**: Integer prices only

---

## DEBUGGING & LOGGING

### Debug Features by Retailer

**HomePro**:
- Saves HTML: `results/debug_homepro_{sku}.html`
- Extensive step-by-step logging

**Thai Watsadu**:
- Logs contamination cleaning steps
- Shows pattern matches

**All Extractors**:
- Return `None` on failure (no exceptions)
- Log extraction methods used
- Track fallback chain

---

## LOCATION-BASED PRICING

### Global House Location Selection

**JavaScript Injection** (`crawl4ai_wrapper.py`):
```javascript
// 1. Click location dropdown
// 2. Click desired location in list
// 3. Wait for price update (6 × 500ms polling)
```

**Price Extraction**:
- Same patterns as standard extraction
- Supports decimals: `[\d,]+(?:\.\d+)?`
- Location name anchored: Selects by Thai name

**See**: `location_price_updater.py` for full implementation

---

## FILE LOCATIONS

- **Main Extractor**: `backend/scraper-url/adws/adw_modules/product_extractor.py` (2923 lines)
- **Schemas**: `backend/scraper-url/adws/adw_modules/product_schemas.py`
- **Crawler**: `backend/scraper-url/adws/adw_modules/crawl4ai_wrapper.py`
- **Price Updater**: `backend/update_prices.py`
- **Location Updater**: `backend/location_price_updater.py`

---

## TESTING

### Test Individual Retailer

```bash
python backend/scraper-url/main.py --url "{URL}" --output-file "test.json"
```

### Test Location Pricing

```bash
python backend/test_location_update_sku.py {TWD_SKU}
```

---

## MAINTENANCE NOTES

### When Adding New Patterns

1. Add retailer-specific pattern in extractor class
2. Test with 10+ products from that retailer
3. Update this documentation with:
   - Pattern regex
   - Key classes/attributes
   - Priority in extraction order
4. Add to price history testing script

### When Retailer Changes Website

1. Identify broken patterns (check error logs)
2. Inspect new HTML structure
3. Add new pattern with higher priority
4. Keep old pattern as fallback
5. Test with old and new pages
6. Document change with date

---

## RECENT CHANGES

### 2026-03-05: Location Pricing Optimizations
- Fixed decimal support for GlobalHouse (all 8 patterns)
- Optimized batch queries (4200+ queries → 1 query)
- Fixed timezone display (UTC → Bangkok +7)

### 2026-02-17: Price Extraction Fixes
- Added Thai Watsadu additional discount badge detection
- Fixed ราคาเดิม (original price) extraction
- Improved pack pricing vs single unit logic

---

**END OF DOCUMENTATION**
