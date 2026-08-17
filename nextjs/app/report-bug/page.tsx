'use client';

import { useSearchParams } from 'next/navigation';
import { useState, useRef, Suspense } from 'react';
import Link from 'next/link';

function ReportBugForm() {
  const searchParams = useSearchParams();
  const origin = searchParams.get('origin') || '/';
  
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    // TODO: Supabase Storage Integration Example
    /* 
    if (file) {
      const { data, error } = await supabase.storage
        .from('bug-reports')
        .upload(`public/${Date.now()}_${file.name}`, file);
    }
    */
    
    console.log({
      title: formData.get('title'),
      description: formData.get('description'),
      origin: formData.get('origin'),
      fileName: file?.name
    });
    
    alert('Bug report submitted. Thank you!');
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-gray-100 py-12 px-4 sm:px-6 lg:px-8 flex justify-center items-start">
      <div className="max-w-2xl w-full space-y-8 bg-[#121212] p-8 sm:p-10 rounded-2xl border border-gray-800 shadow-2xl mt-10">
        
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Report a Bug</h2>
          <p className="text-gray-400 text-sm">Help us improve the platform by describing the issue you encountered.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 mt-8">
          {/* Hidden Origin Field */}
          <input type="hidden" name="origin" value={origin} />

          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-300">
              Issue Title
            </label>
            <input
              type="text"
              name="title"
              id="title"
              required
              placeholder="e.g., App crashes when clicking the submit button"
              className="mt-2 block w-full rounded-lg bg-[#1a1a1a] border border-gray-700 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm px-4 py-3 outline-none transition-all"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-300">
              Steps to Reproduce
            </label>
            <textarea
              name="description"
              id="description"
              rows={5}
              required
              placeholder="1. Go to...&#10;2. Click on...&#10;3. See error..."
              className="mt-2 block w-full rounded-lg bg-[#1a1a1a] border border-gray-700 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm px-4 py-3 outline-none transition-all resize-y"
            />
          </div>

          {/* File Dropzone */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Attach Screenshot or Video (Optional)
            </label>
            <div 
              className={`mt-1 flex justify-center px-6 pt-8 pb-8 border-2 border-dashed rounded-lg transition-colors cursor-pointer ${
                isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 bg-[#1a1a1a] hover:border-gray-500 hover:bg-[#202020]'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="space-y-2 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div className="flex text-sm text-gray-400 justify-center items-center">
                  <span className="relative rounded-md font-medium text-blue-500 hover:text-blue-400 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-offset-[#121212] focus-within:ring-blue-500">
                    Upload a file
                  </span>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">
                  {file ? <span className="text-gray-300">{file.name}</span> : 'PNG, JPG, GIF, MP4 up to 10MB'}
                </p>
              </div>
              <input
                ref={fileInputRef}
                id="file-upload"
                name="file-upload"
                type="file"
                className="sr-only"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              className="w-full flex justify-center py-3.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#121212] focus:ring-blue-500 transition-colors"
            >
              Submit Bug Report
            </button>
            <div className="mt-6 text-center">
              <Link href={origin} className="text-sm text-gray-400 hover:text-white transition-colors">
                Cancel and return to previous page
              </Link>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ReportBug() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center text-white">Loading...</div>}>
      <ReportBugForm />
    </Suspense>
  );
}
