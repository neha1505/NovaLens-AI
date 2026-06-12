import React from 'react';
import { Tag } from 'lucide-react';
import { getImageUrl } from '../services/api';

function ProductCard({ product }) {
  const { name, category, description, price, similarity_score, image_path } = product;
  
  // Format similarity score as percentage
  const similarityPercent = (similarity_score * 100).toFixed(1);

  // Generate badge color based on match strength
  const getMatchBadgeClass = (score) => {
    if (score >= 0.85) return 'bg-emerald-950/80 text-emerald-400 border border-emerald-500/30';
    if (score >= 0.70) return 'bg-blue-950/80 text-blue-400 border border-blue-500/30';
    return 'bg-amber-950/80 text-amber-400 border border-amber-500/30';
  };

  return (
    <div className="glass glass-hover rounded-2xl overflow-hidden flex flex-col group h-full">
      {/* Product Image Container */}
      <div className="relative aspect-square overflow-hidden bg-white border-b border-slate-800/60 flex items-center justify-center p-4">
        <img
          src={getImageUrl(image_path)}
          alt={name}
          className="w-[120px] h-[160px] object-contain crisp-image group-hover:scale-105 transition-transform duration-500 rounded-lg"
          onError={(e) => {
            e.target.onerror = null;
            // Fallback placeholder if server image is unavailable
            e.target.src = 'https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=400&q=80';
          }}
        />
        
        {/* Similarity Score Badge */}
        <div className={`absolute top-3 right-3 px-3 py-1.5 rounded-full text-xs font-bold shadow-lg backdrop-blur-md ${getMatchBadgeClass(similarity_score)}`}>
          {similarityPercent}% Match
        </div>
      </div>

      {/* Product Info */}
      <div className="p-5 flex flex-col flex-grow">
        {/* Category & Price */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-semibold uppercase tracking-wider">
            <Tag size={12} className="text-purple-400" />
            <span>{category}</span>
          </div>
          <span className="text-lg font-bold text-purple-400">
            ₹{price.toLocaleString('en-IN')} <span className="text-xs font-normal text-slate-400">(${(price / 83.0).toFixed(2)})</span>
          </span>
        </div>

        {/* Product Name */}
        <h3 className="text-base font-bold text-slate-100 group-hover:text-purple-300 transition-colors duration-200 line-clamp-1 mb-2">
          {name}
        </h3>

        {/* Product Description */}
        <p className="text-sm text-slate-400 leading-relaxed line-clamp-2 mt-auto">
          {description}
        </p>
      </div>
    </div>
  );
}

export default ProductCard;
