import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import ProductDetails from './pages/ProductDetails';
import Assistant from './pages/Assistant';

function App() {
  return (
    <Router>
      <div className="min-h-screen font-sans relative overflow-hidden">
        {/* Background radial glow visual design is handled globally by body in index.css */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/product/:productId" element={<ProductDetails />} />
          <Route path="/assistant" element={<Assistant />} />
        </Routes>
      </div>
    </Router>
  );
}


export default App;
