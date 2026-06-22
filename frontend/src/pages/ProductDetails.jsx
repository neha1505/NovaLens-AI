import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Tag, Info, ShoppingBag, Eye, Sparkles, RefreshCw, AlertCircle, ExternalLink } from 'lucide-react';
import { getProductDetails, getSimilarProducts, getImageUrl, getProductOutfit, getProductComparison } from '../services/api';
import ProductCard from '../components/ProductCard';

const getFaviconUrl = (retailer) => {
  const domain_map = {
    "Myntra": "myntra.com",
    "Ajio": "ajio.com",
    "Amazon": "amazon.in",
    "Flipkart": "flipkart.com",
    "Tata Cliq": "tatacliq.com",
    "Nykaa Fashion": "nykaafashion.com",
    "Max": "maxfashion.in",
    "Shein": "shein.in",
    "Savana": "savana.com"
  };
  const domain = domain_map[retailer] || "google.com";
  return `https://www.google.com/s2/favicons?sz=64&domain=${domain}`;
};

function ProductDetails() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  // State
  const [product, setProduct] = useState(null);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);

  // Outfit Recommendation Engine State
  const [outfit, setOutfit] = useState(null);
  const [outfitLoading, setOutfitLoading] = useState(true);
  const [outfitError, setOutfitError] = useState(null);

  // Shopping Intelligence State
  const [comparison, setComparison] = useState(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState(null);
  const [activeTab, setActiveTab] = useState('similar'); // 'similar' | 'outfit' | 'compare'

  useEffect(() => {
    let isMounted = true;
    const fetchOutfit = async () => {
      setOutfitLoading(true);
      setOutfitError(null);
      try {
        let viewedIds = [];
        try {
          const stored = localStorage.getItem('novalens_recently_viewed');
          if (stored) {
            const parsed = JSON.parse(stored);
            if (Array.isArray(parsed)) {
              viewedIds = parsed.map(item => item.product_id);
            }
          }
        } catch (e) {
          console.error(e);
        }

        const data = await getProductOutfit(productId, viewedIds);
        if (isMounted) {
          setOutfit(data);
        }
      } catch (err) {
        if (isMounted) {
          console.error("Failed to fetch outfit recommendations:", err);
          setOutfitError(typeof err === 'string' ? err : 'Could not generate styling suggestions.');
        }
      } finally {
        if (isMounted) {
          setOutfitLoading(false);
        }
      }
    };

    fetchOutfit();

    return () => {
      isMounted = false;
    };
  }, [productId]);

  // Shopping Intelligence Fetch Effect
  useEffect(() => {
    if (activeTab === 'compare' && !comparison && !comparisonLoading) {
      const fetchComparison = async () => {
        setComparisonLoading(true);
        setComparisonError(null);
        try {
          const data = await getProductComparison(productId);
          setComparison(data);
        } catch (err) {
          console.error("Failed to fetch product comparison:", err);
          setComparisonError(typeof err === 'string' ? err : 'Could not generate shopping comparison suggestions.');
        } finally {
          setComparisonLoading(false);
        }
      };
      fetchComparison();
    }
  }, [productId, activeTab, comparison, comparisonLoading]);

  // Retrieve similarity score passed from search results if available
  const initialSimilarity = location.state?.similarity_score;

  const saveToRecentlyViewed = (details) => {
    try {
      const storageKey = 'novalens_recently_viewed';
      const existingHistoryStr = localStorage.getItem(storageKey);
      let history = [];
      if (existingHistoryStr) {
        history = JSON.parse(existingHistoryStr);
      }
      
      if (!Array.isArray(history)) {
        history = [];
      }

      // Filter out any duplicate of this product
      history = history.filter(item => item.product_id !== details.product_id);

      // Prepend new item
      const newItem = {
        product_id: details.product_id,
        name: details.name,
        category: details.category,
        price: details.price,
        image_path: details.image_path,
        timestamp: Date.now()
      };

      history.unshift(newItem);

      // Truncate to maximum 20 items
      if (history.length > 20) {
        history = history.slice(0, 20);
      }

      localStorage.setItem(storageKey, JSON.stringify(history));
    } catch (err) {
      console.error("Failed to save product to recently viewed:", err);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setImgLoaded(false);
      setImgError(false);

      try {
        const [details, recommendations] = await Promise.all([
          getProductDetails(productId),
          getSimilarProducts(productId)
        ]);

        if (isMounted) {
          setProduct(details);
          setSimilarProducts(recommendations);
          saveToRecentlyViewed(details);
        }
      } catch (err) {
        if (isMounted) {
          console.error("Failed to load product page details:", err);
          setError(typeof err === 'string' ? err : 'The backend server is offline or the product could not be located. Please make sure the FastAPI server is running on port 8000.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    // Scroll to top on navigation/refresh
    window.scrollTo({ top: 0, behavior: 'smooth' });

    return () => {
      isMounted = false;
    };
  }, [productId]);

  const fallbackImage = 'https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=400&q=80';

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        {/* Sticky Nav Bar */}
        <header className="sticky top-0 z-50 w-full bg-white/72 backdrop-blur-[22px] border-b border-white/45 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <div className="p-1.5 rounded-xl bg-[#16324F]/5 text-[#4A90E2] border border-[#16324F]/10">
                <Eye size={20} />
              </div>
              <span className="font-sans text-lg tracking-tight">
                <span className="font-extrabold text-[#16324F]">NOVA</span>
                <span className="font-medium text-[#4A90E2]">LENS</span>
                <span className="font-bold text-[#16324F]/70 text-[10px] ml-1 uppercase tracking-widest bg-[#16324F]/5 px-1.5 py-0.5 rounded border border-[#16324F]/10">AI</span>
              </span>
            </Link>
          </div>
        </header>

        {/* Shimmer Content Loading State */}
        <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12 animate-pulse">
          <div className="h-6 w-24 bg-slate-200/50 rounded-lg"></div>
          <div className="glass p-8 md:p-12 grid grid-cols-1 md:grid-cols-2 gap-12">
            <div className="h-96 bg-slate-200/50 rounded-3xl w-full"></div>
            <div className="space-y-6 py-4">
              <div className="h-4 bg-slate-200/50 rounded w-1/4"></div>
              <div className="h-8 bg-slate-200/50 rounded w-3/4"></div>
              <div className="h-6 bg-slate-200/50 rounded w-1/3"></div>
              <div className="space-y-3 pt-6 border-t border-[#16324F]/10">
                <div className="h-3 bg-slate-200/50 rounded w-full"></div>
                <div className="h-3 bg-slate-200/50 rounded w-5/6"></div>
                <div className="h-3 bg-slate-200/50 rounded w-4/5"></div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col">
        {/* Sticky Nav Bar */}
        <header className="sticky top-0 z-50 w-full bg-white/72 backdrop-blur-[22px] border-b border-white/45 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <div className="p-1.5 rounded-xl bg-[#16324F]/5 text-[#4A90E2] border border-[#16324F]/10">
                <Eye size={20} />
              </div>
              <span className="font-sans text-lg tracking-tight">
                <span className="font-extrabold text-[#16324F]">NOVA</span>
                <span className="font-medium text-[#4A90E2]">LENS</span>
                <span className="font-bold text-[#16324F]/70 text-[10px] ml-1 uppercase tracking-widest bg-[#16324F]/5 px-1.5 py-0.5 rounded border border-[#16324F]/10">AI</span>
              </span>
            </Link>
          </div>
        </header>

        <main className="flex-grow max-w-3xl w-full mx-auto px-4 py-24">
          <div className="glass p-8 text-center space-y-6 border border-red-100/50">
            <div className="p-4 rounded-full bg-red-50 text-red-500 w-16 h-16 mx-auto flex items-center justify-center border border-red-100 shadow-sm">
              <AlertCircle size={32} />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-extrabold text-[#10243A]">Unable to Load Product</h2>
              <p className="text-sm text-[#5B7083] leading-relaxed max-w-md mx-auto">{error}</p>
            </div>
            <div className="pt-4 flex items-center justify-center gap-4">
              <button 
                onClick={() => navigate('/')}
                className="btn-secondary px-6 py-2.5 text-xs uppercase tracking-wider"
              >
                Go Back Home
              </button>
              <button 
                onClick={() => navigate(0)}
                className="btn-primary px-6 py-2.5 text-xs uppercase tracking-wider flex items-center gap-2"
              >
                <RefreshCw size={12} />
                Retry Load
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const bestPriceOffer = comparison?.results?.find(o => o.is_best_price) || {};
  const bestQualityOffer = comparison?.results?.find(o => o.is_best_quality) || {};
  const bestValueOffer = comparison?.results?.find(o => o.is_best_value) || {};

  const bestPriceRetailer = bestPriceOffer.retailer || 'Retailer';
  const bestQualityRetailer = bestQualityOffer.retailer || 'Retailer';
  const bestOverallRetailer = bestValueOffer.retailer || 'Retailer';

  const similarityPercent = initialSimilarity !== undefined && initialSimilarity !== null
    ? (initialSimilarity * 100).toFixed(0)
    : null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* 1. Sticky Navigation Bar */}
      <header className="sticky top-0 z-50 w-full bg-white/72 backdrop-blur-[22px] border-b border-white/45 shadow-sm transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="p-1.5 rounded-xl bg-[#16324F]/5 text-[#4A90E2] border border-[#16324F]/10">
              <Eye size={20} />
            </div>
            <span className="font-sans text-lg tracking-tight">
              <span className="font-extrabold text-[#16324F]">NOVA</span>
              <span className="font-medium text-[#4A90E2]">LENS</span>
              <span className="font-bold text-[#16324F]/70 text-[10px] ml-1 uppercase tracking-widest bg-[#16324F]/5 px-1.5 py-0.5 rounded border border-[#16324F]/10">AI</span>
            </span>
          </Link>
          
          <nav className="hidden sm:flex items-center gap-6 text-sm font-semibold text-[#5B7083]">
            <Link to="/" className="hover:text-[#16324F] transition-colors">Home</Link>
            <Link to="/assistant" className="hover:text-[#16324F] transition-colors flex items-center gap-1">
              <Sparkles size={14} className="text-[#4A90E2]" />
              AI Assistant
            </Link>
            <span className="text-[#16324F]">Fashion Details</span>
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
        
        {/* 2. Breadcrumb / Back Navigation */}
        <div>
          <button
            onClick={() => navigate('/')}
            className="group flex items-center gap-2 text-xs font-bold text-[#5B7083] hover:text-[#16324F] transition-colors bg-white/40 border border-white/50 px-3.5 py-2 rounded-xl shadow-sm backdrop-blur-sm cursor-pointer"
          >
            <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" />
            Back to Search
          </button>
        </div>

        {/* 3. Product Details Block */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="glass p-6 md:p-10 shadow-xl border border-white/50 relative overflow-hidden"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 md:gap-14 items-start">
            
            {/* Left Frame: Image */}
            <div className="relative bg-white rounded-3xl border border-[#16324F]/10 p-8 flex items-center justify-center min-h-[350px] md:h-[450px] shadow-inner overflow-hidden">
              {!imgLoaded && !imgError && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#EEF5FC]/20 backdrop-blur-sm">
                  <div className="animate-spin rounded-full h-8 w-8 border-3 border-[#16324F]/10 border-t-[#4A90E2]"></div>
                </div>
              )}
              
              <img
                src={imgError ? fallbackImage : getImageUrl(product.image_path)}
                alt={product.name}
                className={`max-h-[300px] md:max-h-[380px] max-w-full object-contain transition-transform duration-500 hover:scale-102 ${
                  imgLoaded ? 'opacity-100' : 'opacity-0'
                }`}
                onLoad={() => setImgLoaded(true)}
                onError={() => {
                  setImgError(true);
                  setImgLoaded(true);
                }}
              />
            </div>

            {/* Right Frame: Metadata Details */}
            <div className="flex flex-col justify-between h-full py-2 space-y-6">
              
              {/* Category Tag & Similarity Score */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="inline-flex items-center gap-1.5 text-[10px] text-[#4A90E2] font-bold uppercase tracking-wider bg-[#16324F]/5 px-3 py-1 rounded-xl border border-[#16324F]/8 shadow-inner">
                  <Tag size={12} />
                  {product.category}
                </div>

                {similarityPercent !== null && (
                  <div className="inline-flex items-center gap-1.5 text-[10px] text-[#16324F] font-bold uppercase tracking-wider bg-[#4A90E2]/10 px-3 py-1 rounded-xl border border-[#4A90E2]/15 shadow-inner">
                    <Sparkles size={11} className="text-[#4A90E2]" />
                    {similarityPercent}% Similarity Match
                  </div>
                )}
              </div>

              {/* Title & Price */}
              <div className="space-y-4">
                <h1 className="text-2xl md:text-3xl font-extrabold text-[#10243A] leading-tight tracking-tight">
                  {product.name}
                </h1>
                
                <div className="flex items-baseline gap-4 pt-1">
                  <span className="text-2xl font-black text-[#10243A]">
                    ₹{product.price.toLocaleString('en-IN')}
                  </span>
                  <span className="text-[10px] font-bold text-[#5B7083] uppercase tracking-wider bg-[#EEF5FC] px-2 py-1 rounded border border-[#16324F]/5">
                    GST Inclusive
                  </span>
                </div>
              </div>

              {/* Description */}
              <div className="space-y-2 border-t border-b border-[#16324F]/8 py-5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#10243A] uppercase tracking-wider">
                  <Info size={14} className="text-[#4A90E2]" />
                  <span>Description</span>
                </div>
                <p className="text-sm text-[#5B7083] font-medium leading-relaxed">
                  {product.description || 'No product description available for this item in the catalog.'}
                </p>
              </div>

              {/* Purchase CTA / Details Table */}
              <div className="space-y-4 pt-2">
                <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between text-xs font-semibold text-[#5B7083]">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#5B7083]">Fashion Item ID:</span>
                    <code className="text-xs font-mono font-bold bg-[#16324F]/5 text-[#16324F] px-2.5 py-1 rounded border border-[#16324F]/10">{product.product_id}</code>
                  </div>
                  <div className="text-[10px] uppercase font-bold text-green-600 bg-green-50 px-2.5 py-1 rounded-md border border-green-200">
                    In Stock
                  </div>
                </div>

                <button 
                  className="btn-search w-full py-4 text-xs uppercase tracking-widest flex items-center justify-center gap-2 shadow-lg"
                  onClick={() => alert(`Purchasing feature simulation for ID: ${product.product_id}`)}
                >
                  <ShoppingBag size={15} />
                  <span>Add to Shopping Bag</span>
                </button>
              </div>

            </div>
          </div>
        </motion.div>

        {/* Modern Glassmorphic Tab Bar Toggle */}
        <div className="flex border-b border-[#16324F]/10 mb-8 p-1 bg-white/30 backdrop-blur-md rounded-2xl border border-white/55 shadow-sm max-w-lg mx-auto sm:mx-0">
          <button
            onClick={() => setActiveTab('similar')}
            className={`flex-grow py-3 px-4 text-[10px] sm:text-xs font-extrabold uppercase tracking-wider rounded-xl transition-all cursor-pointer ${
              activeTab === 'similar'
                ? 'bg-[#16324F] text-white shadow-md'
                : 'text-[#5B7083] hover:text-[#16324F] hover:bg-[#16324F]/5'
            }`}
          >
            Similar Items
          </button>
          <button
            onClick={() => setActiveTab('outfit')}
            className={`flex-grow py-3 px-4 text-[10px] sm:text-xs font-extrabold uppercase tracking-wider rounded-xl transition-all cursor-pointer ${
              activeTab === 'outfit'
                ? 'bg-[#16324F] text-white shadow-md'
                : 'text-[#5B7083] hover:text-[#16324F] hover:bg-[#16324F]/5'
            }`}
          >
            Complete The Look
          </button>
          <button
            onClick={() => setActiveTab('compare')}
            className={`flex-grow py-3 px-4 text-[10px] sm:text-xs font-extrabold uppercase tracking-wider rounded-xl transition-all cursor-pointer ${
              activeTab === 'compare'
                ? 'bg-[#16324F] text-white shadow-md'
                : 'text-[#5B7083] hover:text-[#16324F] hover:bg-[#16324F]/5'
            }`}
          >
            Compare Online
          </button>
        </div>

        {/* Tab View Selection */}
        {activeTab === 'similar' && (
          <div className="space-y-6">
            <div className="border-b border-[#16324F]/20 pb-4 flex items-center justify-between">
              <h2 className="text-lg font-extrabold uppercase tracking-wider text-[#10243A] flex items-center gap-2.5">
                <Sparkles size={18} className="text-[#4A90E2]" />
                <span>Similar Fashion Items</span>
              </h2>
              <span className="text-[10px] font-bold text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-3 py-1 rounded-full shadow-inner">
                Visual Discovery recommendations
              </span>
            </div>

            {similarProducts.length === 0 ? (
              <div className="glass p-12 text-center text-[#5B7083] text-sm font-medium">
                No similar items could be generated for this fashion item.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {similarProducts.map((recProduct) => (
                  <div key={recProduct.product_id} className="h-full">
                    <ProductCard product={recProduct} />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'outfit' && (
          <div className="space-y-6">
            <div className="border-b border-[#16324F]/20 pb-4 flex items-center justify-between">
              <h2 className="text-lg font-extrabold uppercase tracking-wider text-[#10243A] flex items-center gap-2.5">
                <Sparkles size={18} className="text-[#4A90E2]" />
                <span>Complete The Look</span>
              </h2>
              <span className="text-[10px] font-bold text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-3 py-1 rounded-full shadow-inner">
                AI Fashion Stylist suggestions
              </span>
            </div>

            {outfitLoading ? (
              <div className="glass p-12 flex flex-col items-center justify-center space-y-4 animate-pulse">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-[#16324F]/10 border-t-[#4A90E2]"></div>
                <p className="text-xs text-[#5B7083] font-bold uppercase tracking-widest">Generating outfit ideas...</p>
              </div>
            ) : outfitError ? (
              <div className="glass p-8 text-center text-xs font-semibold text-red-600 border border-red-100/50 bg-red-50/20">
                {outfitError}
              </div>
            ) : outfit ? (
              <div className="space-y-6">
                {/* Stylist Notes Card */}
                <div className="glass p-6 md:p-8 border border-white/50 space-y-4 shadow-md bg-white/40">
                  <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#16324F]/10 pb-4">
                    <div className="space-y-1">
                      <h3 className="text-base font-extrabold text-[#10243A]">
                        {outfit.outfit_name}
                      </h3>
                      <p className="text-[10px] text-[#5B7083] font-medium leading-relaxed">
                        Curated matching styling recommendations
                      </p>
                    </div>
                    <div className="inline-flex items-center gap-1.5 text-[10px] text-[#4A90E2] font-bold uppercase tracking-wider bg-[#16324F]/5 px-3 py-1.5 rounded-xl border border-[#16324F]/8 shadow-inner">
                      <Sparkles size={12} />
                      {outfit.style} Style
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-[10px] font-bold text-[#10243A] uppercase tracking-wider">Stylist Notes</p>
                    <p className="text-sm text-[#5B7083] font-medium leading-relaxed">
                      {outfit.explanation}
                    </p>
                  </div>
                </div>

                {/* Recommended Outfit Products Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {outfit.products.map((outfitProduct) => (
                    <div key={outfitProduct.product_id} className="h-full">
                      <ProductCard product={outfitProduct} />
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )}

        {activeTab === 'compare' && (
          <div className="space-y-8 pt-4">
            <div className="border-b border-[#16324F]/20 pb-4 flex items-center justify-between">
              <h2 className="text-lg font-extrabold uppercase tracking-wider text-[#10243A] flex items-center gap-2.5">
                <ShoppingBag size={18} className="text-[#4A90E2]" />
                <span>Compare Online</span>
              </h2>
              <span className="text-[10px] font-bold text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-3 py-1 rounded-full shadow-inner">
                AI Shopping Intelligence Engine
              </span>
            </div>

            {comparisonLoading ? (
              <div className="glass p-12 flex flex-col items-center justify-center space-y-4 animate-pulse">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-[#16324F]/10 border-t-[#4A90E2]"></div>
                <p className="text-xs text-[#5B7083] font-bold uppercase tracking-widest">Scanning trusted retailers...</p>
              </div>
            ) : comparisonError ? (
              <div className="glass p-8 text-center text-xs font-semibold text-red-600 border border-red-100/50 bg-red-50/20">
                {comparisonError}
              </div>
            ) : comparison ? (
              <div className="space-y-8">
                {/* AI Buying Analysis Header Card */}
                <div className="glass p-6 md:p-8 border border-white/50 space-y-6 shadow-md bg-white/40">
                  <div className="flex items-center gap-2 border-b border-[#16324F]/10 pb-4">
                    <Sparkles size={18} className="text-[#4A90E2]" />
                    <h3 className="text-base font-extrabold text-[#10243A] uppercase tracking-wider">AI Buying Analysis</h3>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-4 rounded-2xl bg-green-50/50 border border-green-100/60 flex flex-col justify-between space-y-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-green-700">Best Price Offer</span>
                          <span className="px-2 py-0.5 rounded bg-green-100 text-green-800 text-[8px] font-bold uppercase">Budget Pick</span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed font-medium">
                          {comparison.ai_analysis.best_price_explanation}
                        </p>
                      </div>
                    </div>
                    
                    <div className="p-4 rounded-2xl bg-[#4A90E2]/5 border border-[#4A90E2]/15 flex flex-col justify-between space-y-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#4A90E2]">Best Quality Offer</span>
                          <span className="px-2 py-0.5 rounded bg-[#4A90E2]/15 text-[#16324F] text-[8px] font-bold uppercase">Top Rated</span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed font-medium">
                          {comparison.ai_analysis.best_quality_explanation}
                        </p>
                      </div>
                    </div>

                    <div className="p-4 rounded-2xl bg-amber-50/50 border border-amber-100/60 flex flex-col justify-between space-y-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-700">Best Overall Value</span>
                          <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-[8px] font-bold uppercase">Smart Pick</span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed font-medium">
                          {comparison.ai_analysis.best_overall_explanation}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-[#16324F]/10 space-y-1">
                    <p className="text-[10px] font-bold text-[#10243A] uppercase tracking-wider">Buying Summary Advice</p>
                    <p className="text-xs text-[#5B7083] leading-relaxed font-semibold">
                      {comparison.ai_analysis.buying_summary}
                    </p>
                  </div>
                </div>

                {/* Retailer Offers Comparison List */}
                <div className="space-y-4">
                  <h3 className="text-sm font-extrabold uppercase tracking-wider text-[#10243A]">Verified Retailer Listings (Anti-Fraud Whitelist)</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[...(comparison.results || [])]
                      .sort((a, b) => (b.shopping_score || 0) - (a.shopping_score || 0))
                      .map((offer, idx) => (
                      <div 
                        key={`${offer.retailer}-${offer.product_name}`} 
                        className="glass p-5 border border-white/50 bg-white/40 shadow-sm flex flex-col justify-between space-y-4 hover:shadow-md transition-shadow relative overflow-hidden"
                      >
                        {/* Rank Badge */}
                        <div className="absolute top-4 left-4 flex items-center">
                          <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md ${
                            idx === 0
                              ? 'bg-amber-500 text-white shadow-sm'
                              : 'bg-slate-200 text-slate-700'
                          }`}>
                            #{idx + 1}{idx === 0 ? ' Best Overall Value' : ''}
                          </span>
                        </div>

                        {/* Score Badge */}
                        <div className="absolute top-4 right-4 flex flex-col items-end">
                          <span className="text-[8px] font-bold text-[#5B7083] uppercase tracking-wider">Value Score</span>
                          <span className="text-xs font-black text-[#16324F] bg-[#16324F]/5 border border-[#16324F]/10 px-2 py-0.5 rounded">
                            {Math.round(offer.shopping_score * 100)}/100
                          </span>
                        </div>

                        {/* Detail Frame */}
                        <div className="flex items-start gap-4 pt-7">
                          <div className="w-16 h-16 rounded-xl bg-white border border-[#16324F]/8 flex items-center justify-center p-1.5 shrink-0 overflow-hidden">
                            <img 
                              src={getImageUrl(offer.image_url)} 
                              alt={offer.product_name} 
                              className="max-h-full max-w-full object-contain"
                            />
                          </div>
                          
                          <div className="space-y-1 pr-14">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <img 
                                src={getFaviconUrl(offer.retailer)} 
                                alt={`${offer.retailer} logo`} 
                                className="w-4 h-4 object-contain rounded-sm"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                }}
                              />
                              <span className="text-[9px] font-bold text-[#16324F] uppercase bg-[#16324F]/5 px-2 py-0.5 rounded border border-[#16324F]/8">
                                {offer.retailer}
                              </span>
                              <span className="text-[9px] font-semibold text-[#5B7083]">{offer.brand}</span>
                            </div>
                            <h4 className="text-xs font-bold text-slate-800 line-clamp-2 leading-tight">
                              {offer.product_name}
                            </h4>
                          </div>
                        </div>

                        {/* Ratings and Reviews */}
                        <div className="flex items-center justify-between text-xs py-1 border-t border-b border-[#16324F]/5">
                          <div className="flex items-center gap-1 text-amber-500 font-bold">
                            <span>★</span>
                            <span className="text-slate-700">{offer.rating}</span>
                          </div>
                          <span className="text-[#5B7083] text-[10px] font-semibold">({offer.review_count.toLocaleString()} reviews)</span>
                        </div>

                        {/* Price and Badges */}
                        <div className="flex items-center justify-between">
                          <div className="space-y-0.5">
                            <span className="text-[8px] font-bold text-[#5B7083] uppercase tracking-wider">Offer Price</span>
                            <p className="text-base font-black text-[#10243A]">₹{offer.price.toLocaleString('en-IN')}</p>
                          </div>

                          <div className="flex flex-col items-end gap-1">
                            {offer.is_best_value && (
                              <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[8px] font-extrabold uppercase border border-amber-200">
                                🏆 Best Value
                              </span>
                            )}
                            {offer.is_best_price && (
                              <span className="px-2.5 py-0.5 rounded-full bg-green-100 text-green-800 text-[8px] font-extrabold uppercase border border-green-200">
                                💰 Cheapest
                              </span>
                            )}
                            {offer.is_best_quality && (
                              <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 text-[8px] font-extrabold uppercase border border-blue-200">
                                ⭐ Highest Rated
                              </span>
                            )}
                            {offer.is_most_popular && (
                              <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 text-[8px] font-extrabold uppercase border border-purple-200">
                                🔥 Most Popular
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}

      </main>

      {/* 5. Footer */}
      <footer className="w-full bg-[#EEF5FC] border-t border-[#16324F]/15 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-semibold text-[#5B7083]">
          <div className="flex items-center gap-2">
            <Eye size={16} className="text-[#4A90E2]" />
            <span className="font-extrabold text-[#16324F]">NovaLens AI</span>
            <span className="text-[#5B7083]/40">|</span>
            <span>Multimodal Fashion Discovery Platform</span>
          </div>
          <div className="text-[10px] text-[#5B7083]/50">
            Powered by CLIP + FAISS Similarity Retrieval
          </div>
        </div>
      </footer>
    </div>
  );
}

export default ProductDetails;
