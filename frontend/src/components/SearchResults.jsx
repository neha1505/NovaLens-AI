import React from 'react';
import ProductCard from './ProductCard';
import { EyeOff } from 'lucide-react';

function SearchResults({ results, loading }) {
  if (loading) {
    return (
      <div className="mt-12">
        <h2 className="text-xl font-bold text-slate-200 mb-6 text-center md:text-left">
          Analyzing Image & Searching Index...
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="glass rounded-2xl overflow-hidden h-[380px] flex flex-col animate-pulse">
              <div className="aspect-square bg-slate-800/50 w-full"></div>
              <div className="p-5 flex-grow flex flex-col justify-between">
                <div>
                  <div className="h-4 bg-slate-800/60 rounded w-1/3 mb-4"></div>
                  <div className="h-6 bg-slate-800/60 rounded w-3/4 mb-3"></div>
                </div>
                <div>
                  <div className="h-4 bg-slate-800/60 rounded w-full mb-2"></div>
                  <div className="h-4 bg-slate-800/60 rounded w-2/3"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!results) return null;

  if (results.length === 0) {
    return (
      <div className="mt-12 glass rounded-2xl p-12 text-center max-w-xl mx-auto flex flex-col items-center space-y-4">
        <div className="p-4 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
          <EyeOff size={28} />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-200">No visually similar products found</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-xs mx-auto">
            Try uploading a different image with clearer angles or backgrounds.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-12">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
          <span>Search Results</span>
          <span className="text-sm font-medium text-purple-400 bg-purple-950/40 border border-purple-800/30 px-2.5 py-0.5 rounded-full">
            {results.length} Matches
          </span>
        </h2>
      </div>
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
