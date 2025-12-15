# PriceHawk System Architecture

```mermaid
graph TB
    %% Subgraph definitions
    subgraph "User Layer"
        U[Users]
        UI[Web Browser]
    end

    subgraph "Frontend Layer"
        FE[Next.js Frontend]
        FE_AUTH[Authentication Pages]
        FE_DASH[Dashboard]
        FE_PROD[Product Browser]
        FE_COMP[Comparison View]
        FE_MAN[Manual Comparison]
        FE_REV[Review System]
    end

    subgraph "Backend Layer"
        API[FastAPI Backend]
        AUTH[Authentication Service]
        PROD_API[Product Management API]
        COMP_API[Price Comparison API]
        MATCH_API[Match Management API]
        EXPORT_API[CSV Export API]
    end

    subgraph "Scraping Service"
        SCRAPE[Crawl4AI Scraper]
        CRAWL[Crawl4AI Engine]
        PW[Playwright Browser]
        ADWS[ADWS Wrapper]
    end

    subgraph "Database Layer"
        PG[(PostgreSQL Database)]
        USERS[users table]
        RETAILERS[retailers table]
        PRODUCTS[products table]
        MATCHES[product_matches table]
        PRICE_H[price_history table]
    end

    subgraph "External Services"
        THAI[Thai Watsadu]
        HOME[HomePro]
        DO[Do Home]
        BOON[Boonthavorn]
        GLOBAL[Global House]
        MEGA[MegaHome]
    end

    subgraph "Infrastructure"
        DOCKER[Docker Compose]
        RAILWAY[Railway Deployment]
        NIXPACKS[nixpacks.toml]
    end

    %% Connections - User to Frontend
    U --> UI
    UI --> FE

    %% Frontend internal connections
    FE --> FE_AUTH
    FE --> FE_DASH
    FE --> FE_PROD
    FE --> FE_COMP
    FE --> FE_MAN
    FE --> FE_REV

    %% Frontend to Backend
    FE_AUTH -.->|HTTP/Sessions| AUTH
    FE_DASH -.->|REST API| PROD_API
    FE_PROD -.->|REST API| PROD_API
    FE_COMP -.->|REST API| COMP_API
    FE_MAN -.->|REST API| MATCH_API
    FE_REV -.->|REST API| MATCH_API
    FE_DASH -.->|Download| EXPORT_API

    %% Backend internal connections
    AUTH --> API
    PROD_API --> API
    COMP_API --> API
    MATCH_API --> API
    EXPORT_API --> API

    %% Backend to Database
    API --> PG
    AUTH --> USERS
    PROD_API --> PRODUCTS
    PROD_API --> RETAILERS
    COMP_API --> PRODUCTS
    COMP_API --> PRICE_H
    MATCH_API --> MATCHES
    EXPORT_API --> PRODUCTS

    %% Backend to Scraping
    PROD_API -.->|subprocess call| SCRAPE
    MATCH_API -.->|trigger scrape| SCRAPE

    %% Scraping internal
    SCRAPE --> ADWS
    ADWS --> CRAWL
    CRAWL --> PW

    %% Scraping to External
    PW --> THAI
    PW --> HOME
    PW --> DO
    PW --> BOON
    PW --> GLOBAL
    PW --> MEGA

    %% Database internal
    PG --> USERS
    PG --> RETAILERS
    PG --> PRODUCTS
    PG --> MATCHES
    PG --> PRICE_H

    %% Infrastructure connections
    DOCKER --> PG
    RAILWAY --> API
    NIXPACKS --> RAILWAY

    %% Styling
    classDef userLayer fill:#e1f5fe
    classDef frontendLayer fill:#f3e5f5
    classDef backendLayer fill:#e8f5e9
    classDef scrapingLayer fill:#fff3e0
    classDef databaseLayer fill:#fce4ec
    classDef externalLayer fill:#f1f8e9
    classDef infraLayer fill:#e0f2f1

    class U,UI userLayer
    class FE,FE_AUTH,FE_DASH,FE_PROD,FE_COMP,FE_MAN,FE_REV frontendLayer
    class API,AUTH,PROD_API,COMP_API,MATCH_API,EXPORT_API backendLayer
    class SCRAPE,CRAWL,PW,ADWS scrapingLayer
    class PG,USERS,RETAILERS,PRODUCTS,MATCHES,PRICE_H databaseLayer
    class THAI,HOME,DO,BOON,GLOBAL,MEGA externalLayer
    class DOCKER,RAILWAY,NIXPACKS infraLayer
```

## Architecture Components

### 1. **Frontend Layer (Next.js)**
- **Authentication Pages**: Login/logout functionality
- **Dashboard**: Product overview and statistics
- **Product Browser**: Searchable product listings
- **Comparison View**: Side-by-side product comparisons
- **Manual Comparison**: Tool for adding product comparisons
- **Review System**: Interface for verifying AI matches

### 2. **Backend Layer (FastAPI)**
- **Authentication Service**: Session-based auth with HTTP-only cookies
- **Product Management API**: CRUD operations for products
- **Price Comparison API**: Real-time price comparison logic
- **Match Management API**: Product matching verification
- **CSV Export API**: Data export functionality

### 3. **Scraping Service**
- **Crawl4AI Engine**: AI-powered web scraping
- **Playwright Browser**: Browser automation
- **ADWS Wrapper**: Custom scraper interface
- **Multi-retailer Support**: Handles 6 major Thai retailers

### 4. **Database Schema**
- **users**: User authentication and sessions
- **retailers**: Supported e-commerce platforms
- **products**: Product information and pricing
- **product_matches**: Cross-retailer product relationships
- **price_history**: Historical price tracking

### 5. **External Retailers**
- Thai Watsadu
- HomePro
- Do Home
- Boonthavorn
- Global House
- MegaHome

### 6. **Infrastructure**
- **Docker Compose**: Database containerization
- **Railway**: Cloud deployment platform
- **nixpacks**: Build configuration for Railway

## Data Flow

1. **Scraping Process**:
   - Scheduled/triggered scraping calls Crawl4AI
   - Playwright browser extracts product data
   - Data validated and stored in PostgreSQL

2. **Matching Process**:
   - Products algorithmically matched across retailers
   - AI generates confidence scores
   - Users verify matches through review system

3. **User Interaction**:
   - Web interface provides real-time price comparisons
   - Users can export data via CSV
   - Manual comparison tools available

## Technology Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python, PostgreSQL
- **Scraping**: Crawl4AI, Playwright
- **Deployment**: Railway, Docker
- **Database**: PostgreSQL 16