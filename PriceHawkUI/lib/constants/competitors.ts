/**
 * Competitor Constants
 * Configuration for Thai home improvement retailers
 */

import { CompetitorInfo, CompetitorRetailer } from '@/lib/types/manual-comparison';

export const COMPETITORS: Record<CompetitorRetailer, CompetitorInfo> = {
  HOMEPRO: {
    id: 'HOMEPRO',
    name: 'HomePro',
    nameTh: 'โฮมโปร',
    domain: 'homepro.co.th',
    color: '#1E88E5', // Blue
    logo: '/logos/homepro.png',
  },
  MEGA_HOME: {
    id: 'MEGA_HOME',
    name: 'MegaHome',
    nameTh: 'เมกาโฮม',
    domain: 'megahome.co.th',
    color: '#43A047', // Green
    logo: '/logos/megahome.png',
  },
  BOONTHAVORN: {
    id: 'BOONTHAVORN',
    name: 'Boonthavorn',
    nameTh: 'บุญถาวร',
    domain: 'boonthavorn.com',
    color: '#7B1FA2', // Purple
    logo: '/logos/boonthavorn.png',
  },
  GLOBAL_HOUSE: {
    id: 'GLOBAL_HOUSE',
    name: 'Global House',
    nameTh: 'โกลบอลเฮ้าส์',
    domain: 'globalhouse.co.th',
    color: '#F57C00', // Orange
    logo: '/logos/globalhouse.png',
  },
  DOHOME: {
    id: 'DOHOME',
    name: 'DoHome',
    nameTh: 'ดูโฮม',
    domain: 'dohome.co.th',
    color: '#E64A19', // Deep Orange
    logo: '/logos/dohome.png',
  },
};

// Thai Watsadu brand color (red as shown in image)
export const THAI_WATSADU_COLOR = '#DC2626';

export const COMPETITOR_LIST = Object.values(COMPETITORS);

// Domain patterns for URL validation
export const COMPETITOR_DOMAINS: Record<CompetitorRetailer, string[]> = {
  HOMEPRO: ['homepro.co.th', 'www.homepro.co.th'],
  MEGA_HOME: ['megahome.co.th', 'www.megahome.co.th'],
  BOONTHAVORN: ['boonthavorn.com', 'www.boonthavorn.com'],
  GLOBAL_HOUSE: ['globalhouse.co.th', 'www.globalhouse.co.th', 'global-house.co.th'],
  DOHOME: ['dohome.co.th', 'www.dohome.co.th'],
};

// Thai Watsadu domains for source product validation
export const THAIWATSADU_DOMAINS = [
  'thaiwatsadu.com',
  'www.thaiwatsadu.com',
];
