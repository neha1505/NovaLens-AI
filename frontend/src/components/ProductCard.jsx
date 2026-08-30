import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getImageUrl, getFallbackImage } from '../services/api';
import { Eye } from 'lucide-react';

function ProductCard({ product }) {
  const navigate = useNavigate();
  const { product_id, name, category, price, similarity_score, image_path } = product;
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  
  // Format similarity score as percentage if available
  const similarityPercent = similarity_score !== undefined && similarity_score !== null
    ? (similarity_score * 100).toFixed(0)
    : null;

  return (
    <div 
      onClick={() => navigate(`/product/${product_id}`, { state: { similarity_score } })}
      className="glass glass-hover overflow-hidden flex flex-col group h-full cursor-pointer relative"
    >
      {/* Similarity Score Badge (Top-Right Floating Corner) */}
      {similarityPercent !== null && (
        <div className="absolute top-3 right-3 z-10 bg-white/90 border border-[#16324F]/15 text-[#16324F] text-[10px] font-bold px-2.5 py-1 rounded-full shadow-sm">
          {similarityPercent}% Match
        </div>
      )}

      {/* Product Image Frame */}
      <div className="relative h-[200px] w-full bg-white border-b border-[#16324F]/8 flex items-center justify-center p-4 overflow-hidden">
        {!imgLoaded && !imgError && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#EEF5FC]/20 backdrop-blur-sm">
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-[#16324F]/10 border-t-[#4A90E2]"></div>
          </div>
        )}

        <img
          src={imgError ? getFallbackImage(category, name, product_id) : getImageUrl(image_path, name, category)}
          alt={name}
          loading="lazy"
          className={`w-full h-full object-contain transition-transform duration-500 group-hover:scale-105 ${
            imgLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          onLoad={() => setImgLoaded(true)}
          onError={() => {
            setImgError(true);
            setImgLoaded(true);
          }}
        />
        
        {/* Hover View Detail Overlay */}
        <div className="absolute inset-0 bg-[#16324F]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
          <div className="bg-white/90 px-3.5 py-2 rounded-xl text-xs font-bold text-[#16324F] border border-[#16324F]/12 shadow-md flex items-center gap-1.5 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
            <Eye size={12} className="text-[#4A90E2]" />
            View Details
          </div>
        </div>
      </div>

      {/* Product Info */}
      <div className="p-5 flex flex-col flex-grow justify-between gap-3 bg-white/10">
        <div>
          {/* Category Tag */}
          <div className="text-[9px] text-[#4A90E2] font-bold uppercase tracking-wider bg-[#16324F]/5 px-2 py-0.5 rounded border border-[#16324F]/8 inline-block mb-2.5">
            {category}
          </div>

          {/* Product Name */}
          <h3 className="text-xs font-bold text-[#10243A] group-hover:text-[#4A90E2] transition-colors duration-200 line-clamp-2 leading-tight">
            {name}
          </h3>
        </div>

        <div className="mt-auto pt-3 border-t border-[#16324F]/8 flex items-center justify-between">
          <span className="text-[10px] text-[#5B7083] font-bold uppercase tracking-wider">Price</span>
          <span className="text-xs font-extrabold text-[#10243A]">
            ₹{price.toLocaleString('en-IN')}
          </span>
        </div>
      </div>
    </div>
  );
}

export default ProductCard;
