import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught React Error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-[#EEF5FC]/50">
          <div className="glass p-8 max-w-2xl w-full text-center space-y-6 border border-red-200/60 shadow-xl">
            <div className="p-4 rounded-full bg-red-50 text-red-500 w-16 h-16 mx-auto flex items-center justify-center border border-red-100 shadow-sm">
              <AlertCircle size={32} />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-extrabold text-[#10243A]">Rendering Exception Caught</h2>
              <p className="text-xs text-red-600 font-mono font-bold leading-relaxed bg-red-50 p-3 rounded-xl border border-red-200 text-left overflow-x-auto">
                {this.state.error?.toString() || 'Unknown Error'}
              </p>
              {this.state.errorInfo?.componentStack && (
                <pre className="text-[10px] text-slate-600 font-mono leading-tight bg-slate-100 p-3 rounded-xl text-left overflow-x-auto max-h-40">
                  {this.state.errorInfo.componentStack}
                </pre>
              )}
            </div>
            <button
              onClick={this.handleReload}
              className="btn-primary w-full py-3 text-xs uppercase tracking-wider flex items-center justify-center gap-2"
            >
              <RefreshCw size={14} />
              <span>Reload NovaLens AI</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
