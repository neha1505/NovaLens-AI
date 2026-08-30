import axios from 'axios';

// Dynamic Backend URL for Local Dev & Vercel Production Deployment
const RAW_URL = (import.meta.env.VITE_API_URL || '').trim();
const CLEAN_URL = RAW_URL.replace(/\s+/g, '').replace(/\/api\/?$/, '').replace(/\/$/, '');
const API_BASE_URL = CLEAN_URL ? `${CLEAN_URL}/api` : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'bypass-tunnel-reminder': 'true',
  }
});

export const searchByImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);

  try {
    const response = await api.post('/image-search', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error performing image search:', error);
    // Return structured error message
    throw error.response?.data?.detail || 'An error occurred while connecting to the image search server.';
  }
};

export const searchByText = async (query) => {
  try {
    const response = await api.post('/text-search', { query });
    return response.data;
  } catch (error) {
    console.error('Error performing text search:', error);
    // Return structured error message
    throw error.response?.data?.detail || 'An error occurred while connecting to the text search server.';
  }
};

export const multimodalSearch = async (image, queryText, imageWeight) => {
  const formData = new FormData();
  if (image) {
    formData.append('image', image);
  }
  if (queryText) {
    formData.append('query_text', queryText);
  }
  formData.append('image_weight', imageWeight);

  try {
    const response = await api.post('/multimodal-search', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error performing multimodal search:', error);
    throw error.response?.data?.detail || 'An error occurred while connecting to the multimodal search server.';
  }
};

const FASHION_PHOTOS = {
  DRESSES: [
    "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1612423284934-2850a4ea6b0f?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&w=600&q=80"
  ],
  JACKETS_COATS: [
    "https://images.unsplash.com/photo-1544441893-675973e31985?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1548883354-7622d03aca27?auto=format&fit=crop&w=600&q=80"
  ],
  DENIM: [
    "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1584370848010-d7fe6bc767ec?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=600&q=80"
  ],
  SHIRTS: [
    "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?auto=format&fit=crop&w=600&q=80"
  ],
  PANTS: [
    "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?auto=format&fit=crop&w=600&q=80"
  ],
  DEFAULT: [
    "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?auto=format&fit=crop&w=600&q=80"
  ]
};

export const getImageUrl = (imagePath, name, category, productId) => {
  if (!imagePath) return getFallbackImage(category, name, productId);
  if (imagePath.startsWith("http://") || imagePath.startsWith("https://")) {
    return imagePath;
  }
  
  if (CLEAN_URL && !CLEAN_URL.includes('loca.lt')) {
    let cleanPath = imagePath.replace(/\\/g, '/');
    cleanPath = cleanPath.replace(/^(\/)?(data\/)?(DeepFashion\/)?/, '');
    return `${CLEAN_URL}/images/${cleanPath}`;
  }

  // Use real fashion photography matching product category
  const cat = (category || name || '').toUpperCase();
  let pool = FASHION_PHOTOS.DEFAULT;

  if (cat.includes('DRESS')) pool = FASHION_PHOTOS.DRESSES;
  else if (cat.includes('JACKET') || cat.includes('COAT')) pool = FASHION_PHOTOS.JACKETS_COATS;
  else if (cat.includes('DENIM') || cat.includes('JEAN')) pool = FASHION_PHOTOS.DENIM;
  else if (cat.includes('SHIRT') || cat.includes('BLOUSE')) pool = FASHION_PHOTOS.SHIRTS;
  else if (cat.includes('PANT')) pool = FASHION_PHOTOS.PANTS;

  const keyStr = (productId || name || imagePath || '0');
  const hash = keyStr.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return pool[hash % pool.length];
};

export const getFallbackImage = (category, name, productId) => {
  const cat = (category || 'FASHION').toUpperCase();
  const title = (name || 'Fashion Item').slice(0, 32);

  // Curated gradient palettes per fashion category
  const gradients = {
    DRESSES: ['#FF758C', '#FF7EB3'],
    DENIM: ['#1A2980', '#26D0CE'],
    JACKETS: ['#3A1C71', '#D76D77'],
    SHIRTS: ['#135058', '#F1F2B5'],
    PANTS: ['#20002C', '#CBB4D4'],
    SWEATERS: ['#E65C00', '#F9D423'],
    SKIRTS: ['#EC008C', '#FC6767'],
    DEFAULT: ['#16324F', '#2C5364']
  };

  const palette = Object.keys(gradients).find(k => cat.includes(k)) || 'DEFAULT';
  const [c1, c2] = gradients[palette];

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="500" viewBox="0 0 400 500">
    <defs>
      <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="${c1}" />
        <stop offset="100%" stop-color="${c2}" />
      </linearGradient>
    </defs>
    <rect width="400" height="500" fill="url(#g)" />
    <circle cx="200" cy="190" r="100" fill="#FFFFFF" fill-opacity="0.12" />
    <path d="M200 120 L225 180 L290 180 L238 218 L258 280 L200 242 L142 280 L162 218 L110 180 L175 180 Z" fill="#FFFFFF" fill-opacity="0.25" />
    <text x="200" y="200" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="26" font-weight="900" fill="#FFFFFF" text-anchor="middle" letter-spacing="4">${cat}</text>
    <rect x="30" y="380" width="340" height="75" rx="14" fill="#FFFFFF" fill-opacity="0.94" />
    <text x="200" y="424" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="700" fill="#16324F" text-anchor="middle">${title.replace(/</g, '')}</text>
  </svg>`;

  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
};

export const getProductDetails = async (productId) => {
  try {
    const response = await api.get(`/products/${productId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching product details:', error);
    throw error.response?.data?.detail || 'An error occurred while fetching product details.';
  }
};

export const getSimilarProducts = async (productId) => {
  try {
    const response = await api.get(`/products/${productId}/similar`);
    return response.data;
  } catch (error) {
    console.error('Error fetching similar products:', error);
    throw error.response?.data?.detail || 'An error occurred while fetching similar products.';
  }
};

export const getPersonalizedRecommendations = async (productIds) => {
  try {
    const productIdsStr = productIds.join(',');
    const response = await api.get(`/recommendations?product_ids=${encodeURIComponent(productIdsStr)}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching personalized recommendations:', error);
    throw error.response?.data?.detail || 'An error occurred while fetching recommendations.';
  }
};

export const sendAssistantMessage = async (message, history = [], recentlyViewed = []) => {
  try {
    const payload = {
      message,
      history: history.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text
      })),
      recently_viewed: recentlyViewed
    };
    const response = await api.post('/assistant/chat', payload);
    return response.data;
  } catch (error) {
    console.error('Error in assistant chat request:', error);
    throw error.response?.data?.detail || 'An error occurred while connecting to the AI Assistant service.';
  }
};

export const getProductOutfit = async (productId, recentlyViewedIds = []) => {
  try {
    const idsStr = recentlyViewedIds.join(',');
    const response = await api.get(`/products/${productId}/outfit?recently_viewed=${encodeURIComponent(idsStr)}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching outfit recommendations:', error);
    throw error.response?.data?.detail || 'An error occurred while generating outfit recommendations.';
  }
};

export const getProductComparison = async (productId) => {
  try {
    const response = await api.get(`/products/${productId}/compare`);
    return response.data;
  } catch (error) {
    console.error('Error fetching shopping intelligence comparison:', error);
    throw error.response?.data?.detail || 'An error occurred while loading shopping intelligence comparison.';
  }
};


