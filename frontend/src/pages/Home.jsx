import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ImageUpload from '../components/ImageUpload';
import TextSearch from '../components/TextSearch';
import MultimodalSearch from '../components/MultimodalSearch';
import SearchResults from '../components/SearchResults';
import { searchByImage, searchByText, multimodalSearch, getPersonalizedRecommendations } from '../services/api';
import ProductCard from '../components/ProductCard';
import { Search, Sparkles, RefreshCw, AlertCircle, History, Trash2, Image as ImageIcon, Eye, Github } from 'lucide-react';


// Helper to convert base64 data URL to a File object
const dataURLtoFile = (dataurl, filename) => {
  try {
    const arr = dataurl.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  } catch (e) {
    console.error("Failed to parse data URL to File object:", e);
    return null;
  }
};

function Home() {
  const [searchMode, setSearchMode] = useState('image'); // 'image', 'text', or 'multimodal'
  const [selectedFile, setSelectedFile] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTime, setSearchTime] = useState(null);

  // States to prefill inputs when restoring from history
  const [restoredTextQuery, setRestoredTextQuery] = useState('');
  const [restoredMultimodalFile, setRestoredMultimodalFile] = useState(null);
  const [restoredMultimodalQuery, setRestoredMultimodalQuery] = useState('');
  const [restoredMultimodalWeight, setRestoredMultimodalWeight] = useState(0.7);

  // Search History State (loaded from localStorage)
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('novalens_search_history');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      console.error("Failed to load search history from localStorage:", e);
      return [];
    }
  });

  // Recently Viewed & Recommendation States
  const [recentlyViewed, setRecentlyViewed] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [recsError, setRecsError] = useState(null);

  useEffect(() => {
    const loadHistoryAndRecs = async () => {
      try {
        const stored = localStorage.getItem('novalens_recently_viewed');
        const viewedItems = stored ? JSON.parse(stored) : [];
        setRecentlyViewed(viewedItems);
        
        if (viewedItems && viewedItems.length > 0) {
          setRecsLoading(true);
          setRecsError(null);
          try {
            const ids = viewedItems.map(item => item.product_id);
            const recs = await getPersonalizedRecommendations(ids);
            setRecommendations(recs);
          } catch (err) {
            console.error("Failed to fetch recommendations:", err);
            setRecsError("Failed to fetch recommendations. Make sure the backend server is running.");
          } finally {
            setRecsLoading(false);
          }
        } else {
          setRecommendations([]);
        }
      } catch (e) {
        console.error("Error loading recently viewed or recommendations:", e);
      }
    };
    loadHistoryAndRecs();
  }, []);

  const handleImageSelected = (file) => {
    setSelectedFile(file);
    setError(null);
  };

  const handleImageCleared = () => {
    setSelectedFile(null);
    setSearchResults(null);
    setSearchTime(null);
    setError(null);
  };

  const handleTabChange = (mode) => {
    setSearchMode(mode);
    setSearchResults(null);
    setSelectedFile(null);
    setSearchTime(null);
    setError(null);
    
    // Clear restored prefill references
    setRestoredTextQuery('');
    setRestoredMultimodalFile(null);
    setRestoredMultimodalQuery('');
    setRestoredMultimodalWeight(0.7);
  };

  const saveSearchToHistory = async (type, queryText, file, weight) => {
    try {
      let imagePreview = null;
      let imageName = null;
      
      if (file) {
        imageName = file.name;
        imagePreview = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(file);
        });
      }

      const newItem = {
        id: Date.now().toString(),
        type,
        queryText: queryText || '',
        imageName,
        imagePreview,
        imageWeight: weight !== undefined ? weight : 0.7,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setHistory((prev) => {
        // Prevent duplicate items
        const filtered = prev.filter(item => {
          if (item.type !== newItem.type) return true;
          if (item.type === 'text') return item.queryText.toLowerCase() !== newItem.queryText.toLowerCase();
          if (item.type === 'image') return item.imageName !== newItem.imageName;
          return item.queryText.toLowerCase() !== newItem.queryText.toLowerCase() || item.imageName !== newItem.imageName;
        });

        const updated = [newItem, ...filtered].slice(0, 10);
        localStorage.setItem('novalens_search_history', JSON.stringify(updated));
        return updated;
      });
    } catch (e) {
      console.error("Error saving search item to history:", e);
    }
  };

  const executeImageSearch = async (file) => {
    setLoading(true);
    setError(null);
    setSearchResults(null);
    setSearchTime(null);

    const startTime = performance.now();
    try {
      const data = await searchByImage(file);
      const endTime = performance.now();
      const duration = ((endTime - startTime) / 1000).toFixed(2);
      
      setSearchResults(data);
      setSearchTime(duration);
      
      await saveSearchToHistory('image', null, file);
    } catch (err) {
      setError(typeof err === 'string' ? err : 'The backend server is offline or unreachable. Please verify that the FastAPI server is running on port 8000.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!selectedFile) {
      setError("Please select or drop an image file first.");
      return;
    }
    await executeImageSearch(selectedFile);
  };

  const handleTextSearch = async (query) => {
    setLoading(true);
    setError(null);
    setSearchResults(null);
    setSearchTime(null);

    const startTime = performance.now();
    try {
      const data = await searchByText(query);
      const endTime = performance.now();
      const duration = ((endTime - startTime) / 1000).toFixed(2);
      
      setSearchResults(data);
      setSearchTime(duration);
      
      await saveSearchToHistory('text', query, null);
    } catch (err) {
      setError(typeof err === 'string' ? err : 'The backend server is offline or unreachable. Please verify that the FastAPI server is running on port 8000.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleMultimodalSearch = async ({ image, queryText, imageWeight }) => {
    setLoading(true);
    setError(null);
    setSearchResults(null);
    setSearchTime(null);

    const startTime = performance.now();
    try {
      const data = await multimodalSearch(image, queryText, imageWeight);
      const endTime = performance.now();
      const duration = ((endTime - startTime) / 1000).toFixed(2);
      
      setSearchResults(data);
      setSearchTime(duration);
      
      await saveSearchToHistory('multimodal', queryText, image, imageWeight);
    } catch (err) {
      setError(typeof err === 'string' ? err : 'The backend server is offline or unreachable. Please verify that the FastAPI server is running on port 8000.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRestoreSearch = async (item) => {
    setSearchMode(item.type);
    setError(null);
    setSearchResults(null);
    setSearchTime(null);

    if (item.type === 'text') {
      setRestoredTextQuery(item.queryText);
    } else if (item.type === 'image') {
      if (item.imagePreview && item.imageName) {
        const file = dataURLtoFile(item.imagePreview, item.imageName);
        if (file) {
          setSelectedFile(file);
        }
      }
    } else if (item.type === 'multimodal') {
      let file = null;
      if (item.imagePreview && item.imageName) {
        file = dataURLtoFile(item.imagePreview, item.imageName);
        setRestoredMultimodalFile(file);
      } else {
        setRestoredMultimodalFile(null);
      }
      setRestoredMultimodalQuery(item.queryText || '');
      setRestoredMultimodalWeight(item.imageWeight);
    }
  };

  const handleDeleteHistoryItem = (e, id) => {
    e.stopPropagation();
    setHistory((prev) => {
      const updated = prev.filter(item => item.id !== id);
      localStorage.setItem('novalens_search_history', JSON.stringify(updated));
      return updated;
    });
  };

  const handleClearHistory = () => {
    setHistory([]);
    localStorage.removeItem('novalens_search_history');
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* 1. Sticky Navigation Bar */}
      <header className="sticky top-0 z-50 w-full bg-white/72 backdrop-blur-[22px] border-b border-white/45 shadow-sm transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-xl bg-[#16324F]/5 text-[#4A90E2] border border-[#16324F]/10">
              <Eye size={20} />
            </div>
            <span className="font-sans text-lg tracking-tight">
              <span className="font-extrabold text-[#16324F]">NOVA</span>
              <span className="font-medium text-[#4A90E2]">LENS</span>
              <span className="font-bold text-[#16324F]/70 text-[10px] ml-1 uppercase tracking-widest bg-[#16324F]/5 px-1.5 py-0.5 rounded border border-[#16324F]/10">AI</span>
            </span>
          </div>
          
          <nav className="hidden sm:flex items-center gap-6 text-sm font-semibold text-[#5B7083]">
            <Link to="/" className="text-[#16324F] transition-colors">Home</Link>
            <Link to="/assistant" className="hover:text-[#16324F] transition-colors flex items-center gap-1">
              <Sparkles size={14} className="text-[#4A90E2]" />
              AI Assistant
            </Link>
            <a 
              href="https://github.com/neha1505/NovaLens-AI" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="hover:text-[#16324F] transition-colors flex items-center gap-1"
            >
              <Github size={14} />
              GitHub
            </a>
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        {/* 2. Hero Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center space-y-4 max-w-3xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/70 border border-white/50 text-[#16324F] text-[11px] font-bold uppercase tracking-wider shadow-sm backdrop-blur-md">
            <Sparkles size={13} className="text-[#4A90E2]" />
            <span>AI-Powered Multimodal Fashion Discovery</span>
          </div>
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-[#16324F]">
            NovaLens AI
          </h2>
          <p className="text-base sm:text-lg text-[#5B7083] font-medium leading-relaxed max-w-2xl mx-auto">
            Search and discover clothing using images, text, or multimodal AI. Seamlessly retrieve and browse our visual fashion catalog.
          </p>
        </motion.div>

        {/* 3. Grid Dashboard Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
          {/* Main Content Area */}
          <div className="lg:col-span-3 space-y-8">
            {/* Search Mode Tabs */}
            <div className="flex items-center justify-center">
              <div className="bg-white/40 p-1 rounded-2xl border border-white/50 flex gap-1 shadow-sm backdrop-blur-[22px]">
                <button
                  onClick={() => handleTabChange('image')}
                  className={`px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-all duration-300 cursor-pointer ${
                    searchMode === 'image'
                      ? 'bg-[#16324F] text-white shadow-[0_8px_20px_rgba(22,50,79,0.18)]'
                      : 'text-[#5B7083] hover:text-[#16324F] hover:bg-white/50'
                  }`}
                >
                  Image Search
                </button>
                <button
                  onClick={() => handleTabChange('text')}
                  className={`px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-all duration-300 cursor-pointer ${
                    searchMode === 'text'
                      ? 'bg-[#16324F] text-white shadow-[0_8px_20px_rgba(22,50,79,0.18)]'
                      : 'text-[#5B7083] hover:text-[#16324F] hover:bg-white/50'
                  }`}
                >
                  Text Search
                </button>
                <button
                  onClick={() => handleTabChange('multimodal')}
                  className={`px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-all duration-300 cursor-pointer ${
                    searchMode === 'multimodal'
                      ? 'bg-[#16324F] text-white shadow-[0_8px_20px_rgba(22,50,79,0.18)]'
                      : 'text-[#5B7083] hover:text-[#16324F] hover:bg-white/50'
                  }`}
                >
                  Multimodal Search
                </button>
              </div>
            </div>

            {/* 4. Search Workspace (Floating Glass Container) */}
            <motion.div 
              layout
              className="glass p-8 shadow-xl relative overflow-hidden"
            >
              <AnimatePresence mode="wait">
                <motion.div
                  key={searchMode}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  transition={{ duration: 0.25 }}
                >
                  {searchMode === 'image' && (
                    <div className="space-y-6">
                      <ImageUpload
                        onImageSelected={handleImageSelected}
                        onImageCleared={handleImageCleared}
                        selectedFile={selectedFile}
                      />

                      {error && (
                        <div className="p-4 rounded-2xl bg-red-50 border border-red-200/50 text-red-800 text-sm max-w-xl mx-auto flex gap-3 items-start shadow-sm">
                          <AlertCircle className="flex-shrink-0 text-red-600 mt-0.5" size={18} />
                          <div>
                            <p className="font-bold">Search Exception</p>
                            <p className="text-red-700/90 mt-0.5 leading-relaxed">{error}</p>
                          </div>
                        </div>
                      )}

                      {selectedFile && (
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                          <button
                            onClick={handleSearch}
                            disabled={loading}
                            className="btn-search w-full sm:w-auto px-8 py-3.5 text-sm uppercase tracking-wider"
                          >
                            {loading ? (
                              <RefreshCw className="animate-spin" size={16} />
                            ) : (
                              <Search size={16} />
                            )}
                            <span>{loading ? 'Searching' : 'Find Visually Similar'}</span>
                          </button>

                          <button
                            onClick={handleImageCleared}
                            disabled={loading}
                            className="btn-secondary w-full sm:w-auto px-8 py-3.5 text-sm uppercase tracking-wider"
                          >
                            Clear
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {searchMode === 'text' && (
                    <div className="space-y-6">
                      <TextSearch onSearch={handleTextSearch} loading={loading} initialQuery={restoredTextQuery} />

                      {error && (
                        <div className="p-4 rounded-2xl bg-red-50 border border-red-200/50 text-red-800 text-sm max-w-xl mx-auto flex gap-3 items-start shadow-sm">
                          <AlertCircle className="flex-shrink-0 text-red-600 mt-0.5" size={18} />
                          <div>
                            <p className="font-bold">Search Exception</p>
                            <p className="text-red-700/90 mt-0.5 leading-relaxed">{error}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {searchMode === 'multimodal' && (
                    <div className="space-y-6">
                      <MultimodalSearch 
                        onSearch={handleMultimodalSearch} 
                        loading={loading} 
                        initialFile={restoredMultimodalFile}
                        initialQuery={restoredMultimodalQuery}
                        initialWeight={restoredMultimodalWeight}
                      />

                      {error && (
                        <div className="p-4 rounded-2xl bg-red-50 border border-red-200/50 text-red-800 text-sm max-w-xl mx-auto flex gap-3 items-start shadow-sm">
                          <AlertCircle className="flex-shrink-0 text-red-600 mt-0.5" size={18} />
                          <div>
                            <p className="font-bold">Search Exception</p>
                            <p className="text-red-700/90 mt-0.5 leading-relaxed">{error}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            </motion.div>

            {/* Results Grid Area */}
            <div className="max-w-6xl mx-auto">
              <SearchResults results={searchResults} loading={loading} searchTime={searchTime} searchMode={searchMode} />
            </div>

            {/* Recently Viewed & Personalized Recommendations */}
            {recentlyViewed.length === 0 ? (
              <div className="glass p-12 text-center max-w-xl mx-auto flex flex-col items-center space-y-5 border border-white/50 bg-white/30 mt-12">
                <div className="p-4 rounded-2xl bg-[#16324F]/5 text-[#16324F] border border-[#16324F]/10 shadow-sm">
                  <Sparkles size={28} className="text-[#4A90E2]" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-base font-extrabold text-[#10243A]">Recommended For You</h3>
                  <p className="text-xs text-[#5B7083] font-medium leading-relaxed max-w-sm mx-auto">
                    Start exploring fashion items to receive personalized recommendations.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-12 mt-12">
                {/* Recently Viewed Grid */}
                <div className="space-y-6">
                  <div className="border-b border-[#16324F]/10 pb-4 flex items-center justify-between">
                    <h3 className="text-sm font-extrabold uppercase tracking-wider text-[#10243A] flex items-center gap-2">
                      <History size={16} className="text-[#4A90E2]" />
                      <span>Recently Viewed</span>
                      <span className="text-[10px] font-bold text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-2 py-0.5 rounded-full">
                        Last {recentlyViewed.length} items
                      </span>
                    </h3>
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {recentlyViewed.map((item) => (
                      <div key={item.product_id} className="h-full">
                        <ProductCard product={item} />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommended For You Grid */}
                <div className="space-y-6">
                  <div className="border-b border-[#16324F]/10 pb-4 flex items-center justify-between">
                    <h3 className="text-sm font-extrabold uppercase tracking-wider text-[#10243A] flex items-center gap-2">
                      <Sparkles size={16} className="text-[#4A90E2]" />
                      <span>Recommended For You</span>
                      <span className="text-[10px] font-bold text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-2 py-0.5 rounded-full animate-pulse">
                        Personalized matches
                      </span>
                    </h3>
                  </div>

                  {recsLoading ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                      {Array.from({ length: 4 }).map((_, idx) => (
                        <div key={idx} className="glass rounded-3xl overflow-hidden h-[360px] flex flex-col animate-pulse border border-[#16324F]/8">
                          <div className="h-36 bg-slate-200/50 w-full"></div>
                          <div className="p-5 flex-grow flex flex-col justify-between space-y-4">
                            <div className="space-y-2">
                              <div className="h-3 bg-slate-200/50 rounded w-1/4"></div>
                              <div className="h-5 bg-slate-200/50 rounded w-3/4"></div>
                            </div>
                            <div className="space-y-2 pt-2 border-t border-slate-100/30">
                              <div className="h-3 bg-slate-200/50 rounded w-full"></div>
                              <div className="h-3 bg-slate-200/50 rounded w-2/3"></div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : recsError ? (
                    <div className="glass p-6 text-center text-red-600 text-xs font-semibold border border-red-100/50 bg-red-50/20">
                      {recsError}
                    </div>
                  ) : recommendations.length === 0 ? (
                    <div className="glass p-8 text-center text-[#5B7083] text-xs font-medium">
                      No recommendation matches found.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                      {recommendations.map((rec) => (
                        <div key={rec.product_id} className="h-full">
                          <ProductCard product={rec} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 5. Search History Sidebar Panel */}
          <aside className="lg:col-span-1">
            <div className="glass p-6 shadow-lg sticky top-24 max-h-[85vh] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-[#16324F]/10 pb-4 mb-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#16324F] flex items-center gap-2">
                    <History size={15} className="text-[#4A90E2]" />
                    Search History
                  </h3>
                  {history.length > 0 && (
                    <button
                      onClick={handleClearHistory}
                      className="text-[10px] text-red-600 hover:text-red-800 font-bold border border-red-200 px-2 py-0.5 rounded bg-red-50/50 hover:bg-red-50 transition-all cursor-pointer"
                    >
                      Clear All
                    </button>
                  )}
                </div>

                {history.length === 0 ? (
                  <div className="text-center py-12 text-[#5B7083] text-xs font-medium space-y-2">
                    <History size={24} className="mx-auto text-[#5B7083]/40" />
                    <p>No recent searches yet.</p>
                  </div>
                ) : (
                  <div className="space-y-3 overflow-y-auto max-h-[50vh] pr-1 scrollbar-thin">
                    {history.map((item) => (
                      <div
                        key={item.id}
                        onClick={() => handleRestoreSearch(item)}
                        className="group p-3 rounded-xl bg-white/40 hover:bg-[#EEF5FC]/70 border border-[#16324F]/80 hover:border-[#16324F] transition-all duration-300 cursor-pointer flex items-center justify-between gap-2 shadow-sm"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="flex-shrink-0 p-1.5 rounded-lg bg-[#16324F]/5 text-[#16324F] border border-[#16324F]/10 group-hover:bg-[#16324F]/10 transition-all">
                            {item.type === 'text' && <Search size={13} />}
                            {item.type === 'image' && <ImageIcon size={13} />}
                            {item.type === 'multimodal' && <Sparkles size={13} />}
                          </div>

                          <div className="min-w-0">
                            <p className="text-xs font-extrabold text-[#10243A] group-hover:text-[#16324F] transition-all truncate leading-tight">
                              {item.type === 'text' && `${item.queryText}`}
                              {item.type === 'image' && `${item.imageName}`}
                              {item.type === 'multimodal' && `${item.queryText || 'Fused Query'}`}
                            </p>
                            <span className="text-[9px] font-bold text-[#5B7083] uppercase tracking-wider">
                              {item.type === 'text' && 'Text Search'}
                              {item.type === 'image' && 'Image Search'}
                              {item.type === 'multimodal' && `Fused Search (${Math.round(item.imageWeight * 100)}%)`}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-[9px] font-mono text-[#5B7083]">{item.timestamp}</span>
                          <button
                            onClick={(e) => handleDeleteHistoryItem(e, item.id)}
                            className="text-[#5B7083]/60 hover:text-red-600 p-0.5 rounded transition-colors cursor-pointer"
                            title="Remove"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="border-t border-[#16324F]/80 pt-4 mt-4 text-[10px] text-[#5B7083]/60 text-center font-medium">
                NovaLens AI Local History
              </div>
            </div>
          </aside>
        </div>
      </main>

      {/* 6. Footer Section */}
      <footer className="w-full bg-[#EEF5FC] border-t border-[#16324F]/80 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-semibold text-[#5B7083]">
          <div className="flex items-center gap-2">
            <Eye size={16} className="text-[#4A90E2]" />
            <span className="font-extrabold text-[#16324F]">NovaLens AI</span>
            <span className="text-[#5B7083]/40">|</span>
            <span>Multimodal Fashion Discovery Platform</span>
          </div>
          <div className="flex items-center gap-2">
            <span>Built with:</span>
            <span className="text-[#16324F] font-bold">React</span>
            <span>•</span>
            <span className="text-[#16324F] font-bold">FastAPI</span>
            <span>•</span>
            <span className="text-[#16324F] font-bold">CLIP</span>
            <span>•</span>
            <span className="text-[#16324F] font-bold">FAISS</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Home;
