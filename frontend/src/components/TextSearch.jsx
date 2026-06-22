import React, { useState, useEffect } from 'react';
import { Search, Sparkles } from 'lucide-react';

function TextSearch({ onSearch, loading, initialQuery = '' }) {
  const [query, setQuery] = useState(initialQuery);

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSearch(query.trim());
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (!loading) {
      setQuery(suggestion);
    }
  };

  const suggestions = [
    "blue denim jacket",
    "floral summer dress",
    "formal black blazer",
    "women's winter coat"
  ];

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <div className="absolute left-4 text-[#16324F]/50">
          <Search size={18} />
        </div>
        
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSubmit(e);
            }
          }}
          placeholder="Search fashion items using natural language..."
          className="w-full bg-white/50 border border-[#16324F]/12 rounded-2xl py-4 pl-12 pr-32 text-[#10243A] placeholder-[#5B7083]/70 focus:outline-none focus:border-[#4A90E2] focus:ring-1 focus:ring-[#4A90E2] transition-all font-sans text-sm shadow-inner"
          disabled={loading}
        />
        
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="btn-search absolute right-2 px-6 py-2.5 text-xs uppercase tracking-wider"
        >
          {loading ? "Searching" : "Search"}
        </button>
      </form>
      
      {/* Suggestions List */}
      <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-[#5B7083]">
        <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[#10243A]/80 text-[10px]">
          <Sparkles size={11} className="text-[#4A90E2]" />
          <span>Try:</span>
        </div>
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => handleSuggestionClick(suggestion)}
            disabled={loading}
            className="px-3 py-1 bg-white/40 hover:bg-[#EEF5FC]/70 border border-[#16324F]/10 hover:border-[#16324F]/30 text-[#16324F] font-bold rounded-lg transition-colors cursor-pointer shadow-sm text-[11px]"
          >
            "{suggestion}"
          </button>
        ))}
      </div>
    </div>
  );
}

export default TextSearch;
