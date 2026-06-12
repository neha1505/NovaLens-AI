import React from 'react'
import Home from './pages/Home'

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans relative overflow-hidden">
      {/* Decorative background glow circles */}
      <div className="glow-bg top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-purple-900/10"></div>
      <div className="glow-bg bottom-[-10%] right-[-10%] w-[60vw] h-[60vw] bg-fuchsia-900/10"></div>
      
      <Home />
    </div>
  )
}

export default App
