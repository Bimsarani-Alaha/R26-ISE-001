'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

type CVDType = 'Protanopia' | 'Deuteranopia' | 'Tritanopia';

const CVD_TYPES: CVDType[] = ['Protanopia', 'Deuteranopia', 'Tritanopia'];

const COLOR_MAP: Record<string, string> = {
  blue: '#1f77ff',
  brown: '#8B4513',
  green: '#22aa22',
  red: '#dc143c',
  yellow: '#ffd700'
};

const CVD_DESCRIPTIONS = {
  Protanopia: 'Difficulty distinguishing red, green, and brown. Red appears darker.',
  Deuteranopia: 'Most common type. Difficulty distinguishing green, red, and brown.',
  Tritanopia: 'Rare type. Difficulty distinguishing blue and yellow.'
};

export default function HomePage() {
  const [mounted, setMounted] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [cvdType, setCvdType] = useState<CVDType>('Protanopia');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<{
    color: string;
    confidence: number;
    allConfidences: Record<string, number>;
    simulatedImage: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Process image file
  const processImageFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please upload a valid image file (JPEG, PNG, etc.)');
      return;
    }
    
    setOriginalFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setSelectedImage(reader.result as string);
      setResult(null);
      setError(null);
    };
    reader.readAsDataURL(file);
  };

  // Handle file input change
  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      processImageFile(file);
    }
  };

  // Handle camera capture
  const handleCameraCapture = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      processImageFile(file);
      setIsCameraOpen(false);
    }
  };

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounterRef.current = 0;
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        processImageFile(file);
      } else {
        setError('Please drop a valid image file');
      }
    }
  }, []);

  const handleAnalyze = async () => {
    if (!originalFile) return;

    setIsAnalyzing(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('image', originalFile);
    formData.append('cvdType', cvdType);

    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (data.success) {
        setResult({
          color: data.color,
          confidence: data.confidence,
          allConfidences: data.allConfidences,
          simulatedImage: `data:image/png;base64,${data.simulatedImage}`
        });
      } else {
        setError(data.error || 'Analysis failed');
      }
    } catch (error) {
      console.error('Error:', error);
      setError('Failed to connect to server. Make sure backend is running.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const openCamera = () => {
    setIsCameraOpen(true);
    // Trigger camera input after a short delay to ensure state update
    setTimeout(() => {
      cameraInputRef.current?.click();
    }, 100);
  };

  if (!mounted) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/jpg,image/heic,image/webp"
        onChange={handleImageUpload}
        className="hidden"
      />
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleCameraCapture}
        className="hidden"
      />

      {/* Hero Section */}
      <div className="text-center pt-8 sm:pt-12 pb-4 sm:pb-6 px-4">
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          ColorBlind Vision
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2 text-xs sm:text-sm max-w-md mx-auto">
          Experience how colors are perceived with different types of color blindness
        </p>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        {/* Upload Area - Large & Attractive with Drag & Drop */}
        {!selectedImage ? (
          <div
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={openFilePicker}
            className={`group relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-900 border-2 border-dashed transition-all duration-300 cursor-pointer
              ${isDragging 
                ? 'border-blue-500 bg-blue-100 dark:bg-blue-900/30 scale-[1.01]' 
                : 'border-blue-300 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500'
              }`}
            style={{ minHeight: '350px' }}
          >
            <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
              <div className={`text-6xl sm:text-7xl mb-4 transform transition-transform duration-300 ${isDragging ? 'scale-110' : 'group-hover:scale-110'}`}>
                {isDragging ? '📥' : '📸'}
              </div>
              <h3 className="text-xl sm:text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
                {isDragging ? 'Drop your image here!' : 'Upload Clothing Image'}
              </h3>
              <p className="text-gray-500 dark:text-gray-400 text-xs sm:text-sm">
                Click to browse, drag & drop, or use camera
              </p>
              <div className="flex flex-col sm:flex-row gap-3 mt-6">
                <div className="px-5 py-2 bg-blue-500 text-white rounded-full text-sm font-medium transition-colors">
                  Choose file
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    openCamera();
                  }}
                  className="px-5 py-2 bg-green-500 hover:bg-green-600 text-white rounded-full text-sm font-medium transition-colors shadow-md flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Take Photo
                </button>
              </div>
              <p className="text-gray-400 dark:text-gray-500 text-xs mt-4">
                Supports JPG, PNG, WebP
              </p>
            </div>
            
            {/* Drag overlay */}
            {isDragging && (
              <div className="absolute inset-0 bg-blue-500/10 backdrop-blur-[2px] flex items-center justify-center pointer-events-none">
                <div className="bg-white/90 dark:bg-gray-800/90 rounded-2xl px-6 py-3 text-blue-600 dark:text-blue-400 font-semibold shadow-lg">
                  Drop to upload
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Image Preview & Controls */}
            <div className="grid lg:grid-cols-2 gap-6 md:gap-8">
              {/* Left - Image Preview Large */}
              <div className="space-y-4">
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                  <div className="relative bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 p-3 sm:p-4">
                    <img
                      src={selectedImage}
                      alt="Preview"
                      className="w-full h-auto max-h-[350px] sm:max-h-[400px] object-contain rounded-lg"
                    />
                    <button
                      onClick={openFilePicker}
                      className="absolute top-3 left-3 sm:top-6 sm:left-6 bg-blue-500 hover:bg-blue-600 text-white rounded-full p-2 transition-colors shadow-lg"
                      title="Change image"
                    >
                      <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => {
                        setSelectedImage(null);
                        setOriginalFile(null);
                        setResult(null);
                        setError(null);
                      }}
                      className="absolute top-3 right-3 sm:top-6 sm:right-6 bg-red-500 hover:bg-red-600 text-white rounded-full p-2 transition-colors shadow-lg"
                      title="Remove image"
                    >
                      <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <div className="p-3 sm:p-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-sm text-gray-600 dark:text-gray-400 gap-2">
                      <span>📷 Selected Image</span>
                      <div className="flex gap-2">
                        <button
                          onClick={openCamera}
                          className="text-green-500 hover:text-green-600 font-medium flex items-center gap-1"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          New Photo
                        </button>
                        <button
                          onClick={openFilePicker}
                          className="text-blue-500 hover:text-blue-600 font-medium"
                        >
                          Change file →
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right - Controls */}
              <div className="space-y-5 sm:space-y-6">
                {/* CVD Selector Card */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
                  <h3 className="text-base sm:text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3 sm:mb-4">
                    👁️ Color Vision Type
                  </h3>
                  <div className="space-y-2 sm:space-y-3">
                    {CVD_TYPES.map((type) => (
                      <label
                        key={type}
                        className={`flex items-start p-3 sm:p-4 rounded-xl cursor-pointer transition-all border-2 ${
                          cvdType === type
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }`}
                      >
                        <input
                          type="radio"
                          name="cvdType"
                          value={type}
                          checked={cvdType === type}
                          onChange={(e) => setCvdType(e.target.value as CVDType)}
                          className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0"
                        />
                        <div className="ml-3 flex-1">
                          <div className="font-medium text-gray-800 dark:text-gray-200 text-sm sm:text-base">
                            {type}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {CVD_DESCRIPTIONS[type]}
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Analyze Button */}
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className="w-full py-3 sm:py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-[1.02] shadow-lg text-sm sm:text-base"
                >
                  {isAnalyzing ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4 sm:h-5 sm:w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Analyzing...
                    </span>
                  ) : (
                    '✨ Analyze Color Vision'
                  )}
                </button>

                {error && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-3 sm:p-4">
                    <p className="text-red-600 dark:text-red-400 text-xs sm:text-sm text-center">{error}</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Results Section */}
        {result && (
          <div className="mt-8 sm:mt-12">
            <div className="grid lg:grid-cols-2 gap-6 sm:gap-8">
              {/* Normal Vision Result */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700 transform transition-all hover:shadow-2xl">
                <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-4 sm:px-6 py-3 sm:py-4">
                  <h3 className="text-white font-semibold text-base sm:text-lg flex items-center gap-2">
                    <span>🎨</span> Normal Vision
                  </h3>
                </div>
                <div className="p-4 sm:p-6">
                  <img
                    src={selectedImage!}
                    alt="Normal vision"
                    className="w-full h-auto max-h-[300px] sm:max-h-[350px] object-contain rounded-lg mb-4"
                  />
                  <div className="text-center">
                    <div
                      className="inline-block px-4 sm:px-6 py-1.5 sm:py-2 rounded-full text-white font-bold text-sm sm:text-base mb-3"
                      style={{ backgroundColor: COLOR_MAP[result.color] }}
                    >
                      {result.color.toUpperCase()} • {(result.confidence * 100).toFixed(0)}% confidence
                    </div>
                    <div className="mt-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-1000"
                        style={{
                          width: `${result.confidence * 100}%`,
                          backgroundColor: '#4CAF50'
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* CVD Simulation Result */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700 transform transition-all hover:shadow-2xl">
                <div className="bg-gradient-to-r from-purple-500 to-pink-600 px-4 sm:px-6 py-3 sm:py-4">
                  <h3 className="text-white font-semibold text-base sm:text-lg flex items-center gap-2">
                    <span>👁️</span> {cvdType} Simulation
                  </h3>
                </div>
                <div className="p-4 sm:p-6">
                  <img
                    src={result.simulatedImage}
                    alt="CVD simulation"
                    className="w-full h-auto max-h-[300px] sm:max-h-[350px] object-contain rounded-lg mb-4"
                  />
                  <p className="text-center text-gray-500 dark:text-gray-400 text-xs sm:text-sm">
                    How a person with {cvdType} sees this image
                  </p>
                </div>
              </div>
            </div>

            {/* Detailed Confidence Section */}
            <div className="mt-6 sm:mt-8 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
              <details className="group">
                <summary className="flex items-center justify-between cursor-pointer list-none">
                  <span className="text-base sm:text-lg font-semibold text-gray-800 dark:text-gray-200">
                    📊 Detailed Color Analysis
                  </span>
                  <span className="text-gray-500 group-open:rotate-180 transition-transform text-sm">▼</span>
                </summary>
                <div className="mt-4 sm:mt-6 space-y-3 sm:space-y-4">
                  {Object.entries(result.allConfidences).map(([color, conf]) => (
                    <div key={color}>
                      <div className="flex justify-between text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-1">
                        <span className="capitalize font-medium">{color}</span>
                        <span>{(conf * 100).toFixed(1)}%</span>
                      </div>
                      <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2 sm:h-3 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-1000"
                          style={{
                            width: `${conf * 100}%`,
                            backgroundColor: COLOR_MAP[color]
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            </div>

            {/* New Analysis Button */}
            <div className="mt-6 sm:mt-8 text-center">
              <button
                onClick={() => {
                  setResult(null);
                  setSelectedImage(null);
                  setOriginalFile(null);
                }}
                className="px-6 sm:px-8 py-2.5 sm:py-3 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-xl transition-colors text-sm sm:text-base"
              >
                🔄 Analyze Another Image
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="text-center py-6 sm:py-8 text-gray-400 dark:text-gray-600 text-xs sm:text-sm border-t border-gray-200 dark:border-gray-800 mt-8 sm:mt-12 px-4">
        <p>ColorBlind Vision • AI-powered color blindness simulation for clothing</p>
        <p className="mt-1">📱 Drag & drop • Camera capture • Mobile friendly</p>
      </footer>
    </div>
  );
}