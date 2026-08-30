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

export const getImageUrl = (imagePath, name, category) => {
  if (!imagePath) return getFallbackImage(category, name);
  if (imagePath.startsWith("http://") || imagePath.startsWith("https://")) {
    return imagePath;
  }
  // Sanitize path separators and remove leading redundant prefixes
  let cleanPath = imagePath.replace(/\\/g, '/');
  cleanPath = cleanPath.replace(/^(\/)?(data\/)?(DeepFashion\/)?/, '');
  
  if (CLEAN_URL && !CLEAN_URL.includes('loca.lt')) {
    return `${CLEAN_URL}/images/${cleanPath}`;
  }
  
  return getFallbackImage(category, name);
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


