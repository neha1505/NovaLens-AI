import React, { useState, useRef, useEffect } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';

function ImageUpload({ onImageSelected, onImageCleared, selectedFile }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  // Sync preview when selectedFile changes externally (e.g., cleared from parent)
  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }, [selectedFile]);

  const handleFile = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file (PNG, JPG, JPEG, WEBP).');
      return;
    }
    onImageSelected(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const clearSelection = (e) => {
    e.stopPropagation();
    setPreviewUrl(null);
    onImageCleared();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`glass relative cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-300 ${
          isDragActive
            ? 'border-purple-500 bg-purple-950/20 scale-[1.01]'
            : 'border-slate-700 hover:border-slate-500 bg-slate-900/40'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleChange}
          className="hidden"
        />

        {previewUrl ? (
          <div className="relative group max-w-xs mx-auto">
            <img
              src={previewUrl}
              alt="Preview"
              className="w-full h-48 object-cover rounded-xl shadow-lg border border-slate-700"
            />
            <button
              onClick={clearSelection}
              className="absolute -top-2 -right-2 p-1.5 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors duration-200 shadow-md"
              title="Remove image"
            >
              <X size={16} />
            </button>
            <div className="mt-4 text-sm text-slate-300 font-medium truncate max-w-full">
              {selectedFile?.name}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4 py-4">
            <div className="p-4 rounded-full bg-slate-800/80 text-purple-400 border border-slate-700 shadow-inner group-hover:scale-110 transition-transform">
              <Upload size={32} />
            </div>
            <div>
              <p className="text-base font-semibold text-slate-200">
                Drag and drop your product image here
              </p>
              <p className="text-sm text-slate-400 mt-1">
                or click to browse from files
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500 font-medium justify-center">
              <ImageIcon size={14} />
              <span>Supports PNG, JPG, JPEG, WEBP up to 5MB</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImageUpload;
