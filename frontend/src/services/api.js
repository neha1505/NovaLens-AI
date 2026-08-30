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
  const title = (name || category || 'Fashion Item').slice(0, 30);
  const cleanTitle = title.replace(/[^\w\s-]/g, '').trim();
  const encodedTitle = encodeURIComponent(cleanTitle || 'Fashion Item');
  return `https://placehold.co/400x500/16324F/FFFFFF.png?text=${encodedTitle}`;
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


