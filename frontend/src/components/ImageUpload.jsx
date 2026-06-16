import React, { useState, useRef, useEffect } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';

function ImageUpload({ onImageSelected, onImageCleared, selectedFile }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  // Sync preview when selectedFile changes externally (e.g., cleared or restored)
  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } else {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(selectedFile);
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
        className={`glass relative cursor-pointer rounded-3xl border-2 border-dashed p-8 text-center transition-all duration-300 ${
          isDragActive
            ? 'border-[#4A90E2] bg-[#EEF5FC] scale-[1.01]'
            : 'border-[#16324F]/30 hover:border-[#16324F] bg-white/40 hover:bg-[#EEF5FC]/30 hover:shadow-[0_8px_30px_rgba(22,50,79,0.05)]'
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
              className="w-full h-48 object-contain bg-white rounded-2xl shadow-md border border-[#16324F]/10 p-2"
            />
            <button
              onClick={clearSelection}
              className="absolute -top-2.5 -right-2.5 p-1.5 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors duration-200 shadow-md border border-white"
              title="Remove image"
            >
              <X size={14} />
            </button>
            <div className="mt-4 text-xs text-[#10243A] font-bold truncate max-w-full bg-[#16324F]/5 px-3 py-1.5 rounded-lg border border-[#16324F]/10">
              {selectedFile?.name || 'Restored Image'}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4 py-4">
            <div className="p-4 rounded-2xl bg-[#16324F]/5 text-[#16324F] border border-[#16324F]/10 shadow-inner group-hover:scale-105 transition-all">
              <Upload size={28} />
            </div>
            <div>
              <p className="text-sm font-extrabold text-[#10243A]">
                Upload Product Image
              </p>
              <p className="text-xs text-[#5B7083] font-medium mt-1">
                Drag & Drop or click to browse
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-[#5B7083] font-bold uppercase tracking-wider justify-center">
              <ImageIcon size={12} className="text-[#4A90E2]" />
              <span>PNG, JPG, JPEG, WEBP up to 5MB</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImageUpload;
