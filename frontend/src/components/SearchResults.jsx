import React from 'react';
import ProductCard from './ProductCard';
import { EyeOff, AlertCircle, Database, Clock, Compass } from 'lucide-react';

function SearchResults({ results, loading, searchTime, searchMode }) {
  // Translate searchMode value to friendly text
  const getFriendlyModeName = (mode) => {
    if (mode === 'image') return 'Visual Query';
    if (mode === 'text') return 'Semantic Text';
    if (mode === 'multimodal') return 'Fuzed Modality';
    return 'Search Pipeline';
  };

  if (loading) {
    return (
      <div className="mt-12 space-y-6">
        {/* Shimmer Metrics Cards Placeholder */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div key={idx} className="glass p-5 flex items-center gap-4 animate-pulse">
              <div className="h-10 w-10 rounded-xl bg-slate-200/50 flex-shrink-0"></div>
              <div className="space-y-2 flex-grow">
                <div className="h-3 bg-slate-200/50 rounded w-1/3"></div>
                <div className="h-5 bg-slate-200/50 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>

        {/* Shimmer Product Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="glass rounded-3xl overflow-hidden h-[360px] flex flex-col animate-pulse">
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
      </div>
    );
  }

  if (!results) {
    // Elegant Empty/Welcome State
    return (
      <div className="mt-12 glass p-12 text-center max-w-xl mx-auto flex flex-col items-center space-y-5 border border-white/50 bg-white/30">
        <div className="p-4 rounded-2xl bg-[#16324F]/5 text-[#16324F] border border-[#16324F]/10 shadow-sm">
          <Compass size={28} className="text-[#4A90E2]" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-extrabold text-[#10243A]">Discover Products Instantly</h3>
          <p className="text-sm text-[#5B7083] font-medium leading-relaxed max-w-sm mx-auto">
            Upload an image, enter a search query, or combine both to explore visually and semantically similar catalog products.
          </p>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="mt-12 glass p-12 text-center max-w-xl mx-auto flex flex-col items-center space-y-4 border border-white/50 bg-white/30">
        <div className="p-4 rounded-2xl bg-[#16324F]/5 text-[#5B7083] border border-[#16324F]/10">
          <EyeOff size={28} className="text-[#5B7083]/80" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-extrabold text-[#10243A]">No matching products found</h3>
          <p className="text-xs text-[#5B7083] font-medium max-w-xs mx-auto leading-relaxed">
            Try adjusting your search criteria, queries, or weights to locate items.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-12 space-y-8">
      {/* Search Metrics Dashboard Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Metric 1: Count */}
        <div className="glass p-5 flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="p-3 rounded-2xl bg-[#16324F]/5 text-[#16324F] border border-[#16324F]/10">
            <Database size={20} className="text-[#4A90E2]" />
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#5B7083] leading-none">Results Found</p>
            <p className="text-xl font-extrabold text-[#10243A] mt-1.5">{results.length} Matches</p>
          </div>
        </div>

        {/* Metric 2: Speed */}
        <div className="glass p-5 flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="p-3 rounded-2xl bg-[#16324F]/5 text-[#16324F] border border-[#16324F]/10">
            <Clock size={20} className="text-[#4A90E2]" />
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#5B7083] leading-none">Search Speed</p>
            <p className="text-xl font-extrabold text-[#10243A] mt-1.5">{searchTime || '0.00'} seconds</p>
          </div>
        </div>

        {/* Metric 3: Mode */}
        <div className="glass p-5 flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="p-3 rounded-2xl bg-[#16324F]/5 text-[#16324F] border border-[#16324F]/10">
            <Compass size={20} className="text-[#4A90E2]" />
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#5B7083] leading-none">Search Mode</p>
            <p className="text-xl font-extrabold text-[#10243A] mt-1.5">{getFriendlyModeName(searchMode)}</p>
          </div>
        </div>
      </div>

      {/* Grid Header */}
      <div className="border-b border-[#16324F]/80 pb-4">
        <h3 className="text-sm font-extrabold uppercase tracking-wider text-[#10243A] flex items-center gap-2">
          <span>Visual Matches Results</span>
          <span className="text-[10px] font-bold text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-2 py-0.5 rounded-full">
            Top {results.length} items
          </span>
        </h3>
      </div>

      {/* Product Results Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {results.map((product) => (
          <div key={product.product_id} className="h-full">
            <ProductCard product={product} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default SearchResults;
