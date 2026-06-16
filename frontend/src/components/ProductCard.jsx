import React, { useState } from 'react';
import { getImageUrl } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Tag, Eye } from 'lucide-react';

function ProductCard({ product }) {
  const { name, category, description, price, similarity_score, image_path } = product;
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Format similarity score as percentage
  const similarityPercent = (similarity_score * 100).toFixed(0);

  const fallbackImage = 'https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=400&q=80';

  return (
    <>
      <div 
        onClick={() => setIsModalOpen(true)}
        className="glass glass-hover overflow-hidden flex flex-col group h-full cursor-pointer relative"
      >
        {/* Similarity Score Badge (Top-Right Floating Corner) */}
        <div className="absolute top-3 right-3 z-10 bg-white/90 border border-[#16324F]/15 text-[#16324F] text-[10px] font-bold px-2.5 py-1 rounded-full shadow-sm">
          {similarityPercent}% Match
        </div>

        {/* Product Image Frame */}
        <div className="relative h-[200px] w-full bg-white border-b border-[#16324F]/8 flex items-center justify-center p-4 overflow-hidden">
          {!imgLoaded && !imgError && (
            <div className="absolute inset-0 flex items-center justify-center bg-[#EEF5FC]/20 backdrop-blur-sm">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-[#16324F]/10 border-t-[#4A90E2]"></div>
            </div>
          )}

          <img
            src={imgError ? fallbackImage : getImageUrl(image_path)}
            alt={name}
            loading="lazy"
            className={`w-full h-full object-contain crisp-image transition-transform duration-500 group-hover:scale-105 ${
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
              Quick View
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

      {/* 6. Click-to-Zoom Glass Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#10243A]/15 backdrop-blur-[6px]"
            onClick={() => setIsModalOpen(false)}
          >
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              transition={{ duration: 0.25 }}
              className="glass max-w-2xl w-full overflow-hidden shadow-2xl relative bg-white/95 border border-white/50 p-6 md:p-8"
              onClick={(e) => e.stopPropagation()} // Prevent closing when clicking card body
            >
              {/* Close Button */}
              <button 
                onClick={() => setIsModalOpen(false)}
                className="absolute top-4 right-4 p-2 bg-[#EEF5FC]/80 hover:bg-[#EEF5FC] text-[#16324F] rounded-full transition-all border border-[#16324F]/8 shadow-sm cursor-pointer"
              >
                <X size={15} />
              </button>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                {/* Modal Left: Image */}
                <div className="bg-white rounded-2xl border border-[#16324F]/10 p-6 flex items-center justify-center h-80 shadow-inner">
                  <img 
                    src={imgError ? fallbackImage : getImageUrl(image_path)} 
                    alt={name}
                    className="max-h-full max-w-full object-contain crisp-image" 
                  />
                </div>

                {/* Modal Right: Details */}
                <div className="flex flex-col justify-between h-full py-2 space-y-6">
                  <div className="space-y-4">
                    <div className="inline-flex items-center gap-1.5 text-[9px] text-[#4A90E2] font-bold uppercase tracking-wider bg-[#16324F]/5 px-2.5 py-1 rounded-lg border border-[#16324F]/8">
                      <Tag size={10} />
                      {category}
                    </div>
                    
                    <h4 className="text-lg font-extrabold text-[#10243A] leading-tight">
                      {name}
                    </h4>
                    
                    <div className="space-y-1">
                      <p className="text-[10px] font-bold text-[#5B7083] uppercase tracking-wider">Description</p>
                      <p className="text-xs text-[#5B7083] font-medium leading-relaxed">
                        {description}
                      </p>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-[#16324F]/10 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-[#5B7083] font-semibold">Catalog Price</span>
                      <span className="text-base font-extrabold text-[#10243A]">
                        ₹{price.toLocaleString('en-IN')}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-[#5B7083] font-semibold">Similarity Match</span>
                      <span className="text-xs font-bold text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-3 py-1 rounded-full shadow-inner">
                        {similarityPercent}% Similarity
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

export default ProductCard;
