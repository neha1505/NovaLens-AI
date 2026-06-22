import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Send, Bot, User, ArrowLeft, Eye, RefreshCw, AlertCircle, ShoppingBag, History } from 'lucide-react';
import { sendAssistantMessage } from '../services/api';
import ProductCard from '../components/ProductCard';

function Assistant() {
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  // Core State
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Hi! I'm your AI Fashion Assistant. Ask me for outfit ideas, clothing recommendations, or help finding fashion items.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recentlyViewedIds, setRecentlyViewedIds] = useState([]);
  const [citedProducts, setCitedProducts] = useState([]); // List of products returned from RAG context

  // Load recently viewed product IDs for personalization
  useEffect(() => {
    try {
      const stored = localStorage.getItem('novalens_recently_viewed');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setRecentlyViewedIds(parsed.map(item => item.product_id));
        }
      }
    } catch (e) {
      console.error("Failed to load viewed history for personalization context:", e);
    }
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Suggested starter queries
  const suggestionQueries = [
    "Show me black hoodies for winter.",
    "Suggest a casual college outfit.",
    "Recommend clothing similar to what I've viewed.",
    "What should I wear with a denim jacket?",
    "I need a lightweight jacket for rainy weather.",
    "Find oversized streetwear."
  ];

  // Helper to parse product links in chat text
  const parseMarkdownLinks = (text) => {
    // Matches [Product Name](/product/productId)
    const linkRegex = /\[([^\]]+)\]\(\/product\/([^)]+)\)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(text)) !== null) {
      const matchIndex = match.index;
      // Add text before the link
      if (matchIndex > lastIndex) {
        parts.push(text.substring(lastIndex, matchIndex));
      }

      const displayName = match[1];
      const targetId = match[2];

      parts.push(
        <Link
          key={matchIndex}
          to={`/product/${targetId}`}
          className="text-[#4A90E2] hover:text-[#16324F] font-bold underline transition-colors inline-flex items-center gap-0.5"
        >
          {displayName}
        </Link>
      );

      lastIndex = linkRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  const handleSendMessage = async (textToSend) => {
    const trimmed = textToSend.trim();
    if (!trimmed) return;

    setInputValue('');
    setError(null);
    setLoading(true);

    const userMessageId = Date.now().toString();
    const userMessage = {
      id: userMessageId,
      sender: 'user',
      text: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      // Send message along with history and personalization parameters
      const data = await sendAssistantMessage(trimmed, messages, recentlyViewedIds);
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: data.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update recommendation sidebar cards if products are retrieved
      if (data.products && data.products.length > 0) {
        setCitedProducts(data.products);
      }
    } catch (err) {
      console.error(err);
      setError(typeof err === 'string' ? err : 'The Assistant API is offline. Make sure the backend server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSendMessage(inputValue);
  };

  const handleSuggestionClick = (queryText) => {
    handleSendMessage(queryText);
  };

  const clearChatHistory = () => {
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        text: "Hi! I'm your AI Fashion Assistant. Ask me for outfit ideas, clothing recommendations, or help finding fashion items.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setCitedProducts([]);
    setError(null);
  };

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
            <span className="text-[#16324F]">AI Assistant</span>
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col space-y-6">
        
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="group flex items-center gap-2 text-xs font-bold text-[#5B7083] hover:text-[#16324F] transition-colors bg-white/40 border border-white/50 px-3.5 py-2 rounded-xl shadow-sm backdrop-blur-sm cursor-pointer"
          >
            <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" />
            Back
          </button>
          
          <button
            onClick={clearChatHistory}
            className="text-[10px] text-red-600 hover:text-red-800 font-bold border border-red-200 px-3 py-1.5 rounded-xl bg-red-50/50 hover:bg-red-50 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <History size={12} />
            Clear Chat
          </button>
        </div>

        {/* Dashboard layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-stretch flex-grow min-h-[70vh]">
          
          {/* Chat Workspace (Left 2 Columns) */}
          <div className="lg:col-span-2 flex flex-col glass p-5 md:p-6 border border-white/50 relative overflow-hidden shadow-lg justify-between h-[70vh] min-h-[500px]">
            
            {/* Scrollable Conversation Panel */}
            <div className="flex-grow overflow-y-auto space-y-4 pr-2 scrollbar-thin max-h-[calc(70vh-140px)]">
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`flex items-start gap-3.5 max-w-[85%] ${
                      msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''
                    }`}
                  >
                    {/* Icon frames */}
                    <div className={`p-2 rounded-xl border flex-shrink-0 shadow-sm ${
                      msg.sender === 'user'
                        ? 'bg-[#16324F] text-white border-[#16324F]/10'
                        : 'bg-[#4A90E2]/10 text-[#4A90E2] border-[#4A90E2]/15'
                    }`}>
                      {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                    </div>

                    {/* Bubble body */}
                    <div className="space-y-1">
                      <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm font-medium ${
                        msg.sender === 'user'
                          ? 'bg-[#16324F] text-white rounded-tr-none'
                          : 'bg-[#EEF5FC] text-[#10243A] rounded-tl-none border border-[#16324F]/5'
                      }`}>
                        <p className="whitespace-pre-wrap">{parseMarkdownLinks(msg.text)}</p>
                      </div>
                      
                      {/* Timestamp */}
                      <p className={`text-[9px] font-mono text-[#5B7083]/60 ${
                        msg.sender === 'user' ? 'text-right' : 'text-left'
                      }`}>
                        {msg.timestamp}
                      </p>
                    </div>
                  </motion.div>
                ))}

                {/* Loading / Typing anim state */}
                {loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-center gap-3.5 max-w-[85%]"
                  >
                    <div className="p-2 rounded-xl bg-[#4A90E2]/10 text-[#4A90E2] border border-[#4A90E2]/15 flex-shrink-0 animate-pulse">
                      <Bot size={14} />
                    </div>
                    <div className="bg-[#EEF5FC] border border-[#16324F]/5 p-4 rounded-2xl rounded-tl-none flex items-center gap-1.5 shadow-sm">
                      <div className="w-1.5 h-1.5 bg-[#4A90E2] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-1.5 h-1.5 bg-[#4A90E2] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-1.5 h-1.5 bg-[#4A90E2] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              
              <div ref={messagesEndRef} />
            </div>

            {/* Bottom Form and Suggestions Area */}
            <div className="border-t border-[#16324F]/10 pt-4 mt-2 space-y-4">
              
              {/* Query suggestion chips - Only show when input is empty and loading is false */}
              {!inputValue && !loading && messages.length === 1 && (
                <div className="flex flex-wrap gap-2">
                  {suggestionQueries.map((queryText, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(queryText)}
                      className="text-[10px] font-bold text-[#16324F] bg-[#16324F]/5 hover:bg-[#16324F]/10 border border-[#16324F]/8 px-3 py-1.5 rounded-full cursor-pointer transition-all duration-200"
                    >
                      {queryText}
                    </button>
                  ))}
                </div>
              )}

              {error && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200/50 text-red-800 text-xs flex gap-2 items-center shadow-sm">
                  <AlertCircle className="flex-shrink-0 text-red-600" size={14} />
                  <span>{error}</span>
                </div>
              )}

              {/* Chat Input Field */}
              <form onSubmit={handleFormSubmit} className="flex gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask for outfit ideas, styling advice, or specific clothing..."
                  disabled={loading}
                  className="flex-grow bg-[#EEF5FC] border border-[#16324F]/10 hover:border-[#16324F]/20 focus:border-[#4A90E2] focus:ring-1 focus:ring-[#4A90E2]/25 outline-none rounded-xl px-4 py-3 text-xs font-semibold placeholder-[#5B7083]/60 transition-all text-[#10243A] disabled:opacity-50"
                />
                
                <button
                  type="submit"
                  disabled={loading || !inputValue.trim()}
                  className="btn-search p-3 rounded-xl flex items-center justify-center flex-shrink-0 cursor-pointer disabled:opacity-50 disabled:pointer-events-none"
                >
                  <Send size={15} />
                </button>
              </form>
            </div>

          </div>

          {/* RAG Product Catalog recommendations sidebar (Right 1 Column) */}
          <div className="lg:col-span-1 flex flex-col glass p-5 md:p-6 border border-white/50 shadow-lg justify-between h-[70vh] min-h-[500px]">
            <div className="space-y-4 h-full flex flex-col">
              
              {/* Header */}
              <div className="border-b border-[#16324F]/10 pb-3 flex items-center justify-between">
                <h3 className="text-xs font-extrabold uppercase tracking-wider text-[#10243A] flex items-center gap-2">
                  <Sparkles size={14} className="text-[#4A90E2]" />
                  <span>Referenced Products</span>
                </h3>
                <span className="text-[9px] font-bold text-[#16324F] bg-[#16324F]/5 px-2 py-0.5 rounded-full border border-[#16324F]/10">
                  RAG catalog context
                </span>
              </div>

              {/* Products content area */}
              <div className="flex-grow overflow-y-auto space-y-4 pr-1 scrollbar-thin max-h-[calc(70vh-80px)]">
                {citedProducts.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center text-[#5B7083]/60 px-4 py-16 space-y-3">
                    <div className="p-3 bg-[#16324F]/5 rounded-xl border border-[#16324F]/10">
                      <ShoppingBag size={20} className="text-[#5B7083]/40" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-bold text-[#10243A]/80">No Referenced Items</p>
                      <p className="text-[10px] font-medium leading-relaxed max-w-[180px] mx-auto">
                        Ask the assistant to recommend clothes to view products here.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4">
                    {citedProducts.map((product) => (
                      <div key={product.product_id} className="relative group transition-all duration-300">
                        {/* Compact card layout for chat sidebar context */}
                        <div className="h-full transform hover:scale-[1.01]">
                          <ProductCard product={product} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          </div>

        </div>

      </main>

      {/* Footer */}
      <footer className="w-full bg-[#EEF5FC] border-t border-[#16324F]/15 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-semibold text-[#5B7083]">
          <div className="flex items-center gap-2">
            <Bot size={16} className="text-[#4A90E2]" />
            <span className="font-extrabold text-[#16324F]">NovaLens AI Assistant</span>
            <span className="text-[#5B7083]/40">|</span>
            <span>Fashion Styling & RAG Retrieval Advisor</span>
          </div>
          <div className="text-[10px] text-[#5B7083]/50">
            Powered by CLIP + FAISS + Gemini LLM Grounding
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Assistant;
