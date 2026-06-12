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

export const getImageUrl = (imagePath) => {
  return `http://localhost:8000/images/${imagePath}`;
};
