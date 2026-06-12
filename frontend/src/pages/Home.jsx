import React, { useState } from 'react';
import ImageUpload from '../components/ImageUpload';
import SearchResults from '../components/SearchResults';
import { searchByImage } from '../services/api';
import { Search, Sparkles, RefreshCw, AlertCircle } from 'lucide-react';

function Home() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleImageSelected = (file) => {
    setSelectedFile(file);
    setError(null);
  };

  const handleImageCleared = () => {
    setSelectedFile(null);
    setSearchResults(null);
    setError(null);
  };

  const handleSearch = async () => {
    if (!selectedFile) {
      setError("Please select or drop an image file first.");
      return;
    }

    setLoading(true);
    setError(null);
    setSearchResults(null);

    try {
      const data = await searchByImage(selectedFile);
      setSearchResults(data);
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Failed to search the product index. Please ensure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
      {/* Header Section */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-950/50 border border-purple-800/40 text-purple-300 text-xs font-semibold uppercase tracking-wider mb-4 animate-pulse">
          <Sparkles size={14} />
          <span>Phase 1 Visual Search</span>
        </div>
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-purple-400 bg-clip-text text-transparent">
          NovaLens AI
        </h1>
        <p className="mt-3 text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto font-medium font-sans">
          AI-Powered Visual Product Search
        </p>
        <p className="mt-2 text-xs text-slate-500 max-w-lg mx-auto">
          Upload any product image to discover matching catalog items instantly using CLIP embeddings and FAISS index.
        </p>
      </div>

      {/* Upload and Control Card */}
      <div className="glass rounded-3xl p-8 max-w-3xl mx-auto shadow-2xl">
        <ImageUpload
          onImageSelected={handleImageSelected}
          onImageCleared={handleImageCleared}
          selectedFile={selectedFile}
        />

        {/* Error Alert Box */}
        {error && (
          <div className="mt-6 flex items-start gap-3 p-4 rounded-xl bg-red-950/40 border border-red-500/20 text-red-200 text-sm max-w-xl mx-auto">
            <AlertCircle className="flex-shrink-0 text-red-400 mt-0.5" size={18} />
            <div>
              <p className="font-semibold">Search Failed</p>
              <p className="text-slate-300 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Buttons / Controls */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          {selectedFile && (
            <>
              <button
                onClick={handleSearch}
                disabled={loading}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-gradient-to-r from-purple-600 to-brand-600 hover:from-purple-500 hover:to-brand-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 text-white font-bold rounded-xl shadow-lg shadow-purple-900/20 transition-all duration-300 hover:shadow-purple-700/35 hover:scale-[1.02] active:scale-[0.98]"
              >
                {loading ? (
                  <RefreshCw className="animate-spin" size={18} />
                ) : (
                  <Search size={18} />
                )}
                <span>{loading ? 'Searching...' : 'Find Visually Similar'}</span>
              </button>

              <button
                onClick={handleImageCleared}
                disabled={loading}
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 text-slate-300 font-semibold rounded-xl transition-all duration-200"
              >
                Clear
              </button>
            </>
          )}
        </div>
      </div>

      {/* Results grid */}
      <div className="max-w-6xl mx-auto">
        <SearchResults results={searchResults} loading={loading} />
      </div>
    </div>
  );
}

export default Home;
