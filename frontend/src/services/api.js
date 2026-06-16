import axios from 'axios';

// Backend runs on http://localhost:8000
const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
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

export const getImageUrl = (imagePath) => {
  return `http://localhost:8000/images/${imagePath}`;
};
