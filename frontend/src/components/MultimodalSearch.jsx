import React, { useState, useRef, useEffect } from 'react';
import {
  Upload,
  X,
  Image as ImageIcon,
  Search,
  Sliders,
  Sparkles,
  RefreshCw
} from 'lucide-react';

function MultimodalSearch({ onSearch, loading, initialFile = null, initialQuery = '', initialWeight = 0.7 }) {
  const [selectedFile, setSelectedFile] = useState(initialFile);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [query, setQuery] = useState(initialQuery);
  const [imageWeight, setImageWeight] = useState(initialWeight);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    setSelectedFile(initialFile);
    if (initialFile) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(initialFile);
    } else {
      setPreviewUrl(null);
    }
  }, [initialFile]);

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  useEffect(() => {
    setImageWeight(initialWeight);
  }, [initialWeight]);

  const handleFile = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file (PNG, JPG, JPEG, WEBP).');
      return;
    }
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const clearImage = (e) => {
    if (e) e.stopPropagation();
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const hasImage = !!selectedFile;
    const hasText = !!query.trim();

    if (!hasImage && !hasText) {
      alert("Please upload an image, enter query text, or both.");
      return;
    }

    onSearch({
      image: selectedFile,
      queryText: query.trim() || null,
      imageWeight: parseFloat(imageWeight)
    });
  };

  const handleClearAll = () => {
    clearImage();
    setQuery('');
    setImageWeight(0.7);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 w-full max-w-2xl mx-auto">
      {/* 1. Image Upload Area */}
      <div className="space-y-2">
        <label className="block text-xs font-bold uppercase tracking-wider text-[#10243A] leading-none">Upload Reference Image (Optional)</label>
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative cursor-pointer rounded-3xl border-2 border-dashed p-6 text-center transition-all duration-300 ${isDragActive
              ? 'border-[#4A90E2] bg-[#EEF5FC] scale-[1.01]'
              : 'border-[#16324F]/30 hover:border-[#16324F] bg-white/40 hover:bg-[#EEF5FC]/30 hover:shadow-sm'
            }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleChange}
            className="hidden"
            disabled={loading}
          />

          {previewUrl ? (
            <div className="relative group max-w-xs mx-auto">
              <img
                src={previewUrl}
                alt="Preview"
                className="w-full h-32 object-contain bg-white rounded-2xl border border-[#16324F]/10 p-1.5 shadow-sm"
              />
              <button
                type="button"
                onClick={clearImage}
                className="absolute -top-2 -right-2 p-1 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors shadow-md z-10 border border-white"
                title="Remove image"
                disabled={loading}
              >
                <X size={12} />
              </button>
              <div className="mt-2 text-[10px] font-bold text-[#5B7083] truncate max-w-full">
                {selectedFile?.name || 'Restored Image'}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-2 py-2">
              <div className="p-3 rounded-2xl bg-[#16324F]/5 text-[#16324F] border border-[#16324F]/10 shadow-inner">
                <Upload size={20} />
              </div>
              <div>
                <p className="text-xs font-extrabold text-[#10243A]">
                  Drag & drop image here or click to browse
                </p>
              </div>
              <div className="flex items-center gap-1.5 text-[9px] text-[#5B7083] font-bold uppercase tracking-wider justify-center">
                <ImageIcon size={11} className="text-[#4A90E2]" />
                <span>PNG, JPG, JPEG, WEBP up to 5MB</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2. Text Modifier Area */}
      <div className="space-y-2">
        <label className="block text-xs font-bold uppercase tracking-wider text-[#10243A] leading-none">Text Modifier (Optional)</label>
        <div className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. similar but black, sleeveless, striped shirt..."
            className="w-full bg-white/50 border border-[#16324F]/12 rounded-2xl py-3.5 px-4 text-[#10243A] placeholder-[#5B7083]/70 focus:outline-none focus:border-[#4A90E2] focus:ring-1 focus:ring-[#4A90E2] transition-all font-sans text-sm shadow-inner"
            disabled={loading}
          />
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-[#5B7083] font-bold uppercase tracking-wider">
          <Sparkles size={11} className="text-[#4A90E2]" />
          <span>Modifier phrases <span className="italic text-[#4A90E2]">"similar but black"</span> alter embeddings semantically.</span>
        </div>
      </div>

      {/* 3. Image Influence Slider */}
      {selectedFile && query.trim() && (
        <div className="space-y-4">
          <div className="space-y-3 p-4 rounded-2xl bg-white/40 border border-[#16324F]/10 shadow-sm">
            <div className="flex justify-between items-center text-xs">
              <span className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[#10243A]">
                <Sliders size={14} className="text-[#4A90E2]" />
                Weight Control
              </span>
              <span className="text-[10px] font-bold font-mono text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-2 py-0.5 rounded">
                Image Influence: {Math.round(imageWeight * 100)}%
              </span>
            </div>

            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={imageWeight}
              onChange={(e) => setImageWeight(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#16324F] focus:outline-none"
              disabled={loading}
            />
            <div className="flex justify-between text-[9px] text-[#5B7083] font-extrabold uppercase tracking-wider">
              <span>Text Focus</span>
              <span>Balanced</span>
              <span>Image Focus</span>
            </div>
          </div>

          {/* Explanation Panel */}
          <div className="p-4 rounded-2xl bg-[#EEF5FC] border border-[#16324F]/10 space-y-2 text-xs">
            <div className="font-extrabold text-[#16324F] flex items-center gap-1.5 uppercase tracking-wider text-[10px]">
              <Sparkles size={13} className="text-[#4A90E2]" />
              Query Fusion Explanation
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[#5B7083] font-semibold leading-relaxed">
              <div>Image Influence: <span className="text-[#10243A] font-bold">{Math.round(imageWeight * 100)}%</span></div>
              <div>Text Influence: <span className="text-[#10243A] font-bold">{Math.round((1.0 - imageWeight) * 100)}%</span></div>
              <div className="sm:text-right">Method: <span className="text-[#10243A] font-bold">Weighted Embedding Fusion</span></div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
        <button
          type="submit"
          disabled={loading || (!selectedFile && !query.trim())}
          className="btn-search w-full sm:w-auto px-8 py-3.5 text-sm uppercase tracking-wider"
        >
          {loading ? (
            <RefreshCw className="animate-spin" size={16} />
          ) : (
            <Search size={16} />
          )}
          <span>{loading ? 'Searching' : 'Multimodal Search'}</span>
        </button>

        {(selectedFile || query.trim()) && (
          <button
            type="button"
            onClick={handleClearAll}
            disabled={loading}
            className="btn-secondary w-full sm:w-auto px-8 py-3.5 text-sm uppercase tracking-wider"
          >
            Clear All
          </button>
        )}
      </div>
    </form>
  );
}

export default MultimodalSearch;
