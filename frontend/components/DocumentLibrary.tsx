"use client";

import React from 'react';
import { Document } from '@/app/page';
import { Check, Loader, AlertCircle } from 'lucide-react';

interface DocumentLibraryProps {
  uploadedFiles: Document[];
  activeFiles: string[];
  setActiveFiles: React.Dispatch<React.SetStateAction<string[]>>;
}

const DocumentLibrary: React.FC<DocumentLibraryProps> = ({ uploadedFiles, activeFiles, setActiveFiles }) => {

  const handleCheckboxChange = (filename: string) => {
    setActiveFiles(prev => 
      prev.includes(filename) 
        ? prev.filter(name => name !== filename)
        : [...prev, filename]
    );
  };

  if (uploadedFiles.length === 0) {
    return (
      <div className="text-center text-slate-500 mt-4">
        <p>Belum ada dokumen yang diunggah.</p>
        <p className="text-sm">Unggah dokumen di atas untuk memulai analisis.</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto pr-2">
      <ul className="space-y-3">
        {uploadedFiles.map(file => (
          <li key={file.name} className="flex items-center justify-between p-3 bg-slate-50/80 rounded-lg shadow-sm border border-slate-200/80">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <input
                type="checkbox"
                id={`checkbox-${file.name}`}
                checked={activeFiles.includes(file.name)}
                onChange={() => handleCheckboxChange(file.name)}
                disabled={file.status !== 'completed'}
                className="h-5 w-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 disabled:opacity-50 cursor-pointer"
              />
              <label htmlFor={`checkbox-${file.name}`} className="text-sm font-medium text-slate-800 truncate cursor-pointer" title={file.name}>
                {file.name}
              </label>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0 ml-2">
              {file.status === 'processing' && <Loader className="w-4 h-4 text-slate-400 animate-spin" />}
              {file.status === 'completed' && <Check className="w-4 h-4 text-green-500" />}
              {file.status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
              <span className={`text-xs font-semibold capitalize ${
                file.status === 'completed' ? 'text-green-600' :
                file.status === 'processing' ? 'text-slate-500' :
                'text-red-600'
              }`}>
                {file.status}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DocumentLibrary;
