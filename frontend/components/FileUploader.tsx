"use client";

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFile } from '@/lib/api';
import { FileUp, Loader, XCircle } from 'lucide-react';

interface FileUploaderProps {
  onUploadComplete: (filename: string, textContent: string) => void;
  isChatActive: boolean;
}

const FileUploader: React.FC<FileUploaderProps> = ({ onUploadComplete, isChatActive }) => {
  const [status, setStatus] = useState<'idle' | 'uploading' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleUpload = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setStatus('uploading');
    setError(null);
    setProgress(0);
    setUploadedFile(file);

    try {
      const { filename } = await uploadFile(file, setProgress);
      setStatus('idle'); // Reset status after completion
      setProgress(100);
      onUploadComplete(filename, ""); // Backend is sync, activate chat immediately
    } catch (uploadError: any) {
      setError(uploadError.message || 'An unexpected error occurred.');
      setStatus('error');
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop: handleUpload,
    disabled: status === 'uploading' || isChatActive,
    multiple: false,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    }
  });

  if (status === 'uploading' || status === 'error') {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-center p-4">
        <div className="mb-4">
          {status === 'error' ? (
            <XCircle className="h-12 w-12 text-red-500" />
          ) : (
            <Loader className="h-12 w-12 text-blue-500 animate-spin" />
          )}
        </div>
        <p className="text-lg font-medium text-slate-800 break-all">
          {status === 'error' ? 'Terjadi Kesalahan' : 'Sedang Menganalisis'}
        </p>
        <p className="text-sm text-slate-600 mb-4 break-all">
          {status === 'error' ? error : uploadedFile?.name}
        </p>
        {status === 'uploading' && (
            <div className="w-full bg-slate-200 rounded-full h-2.5">
                <div className="bg-blue-500 h-2.5 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
            </div>
        )}
      </div>
    );
  }

  return (
    <div {...getRootProps()} className={`w-full h-full border-2 border-dashed rounded-xl flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 
      ${isDragActive ? 'border-blue-500 bg-blue-100/50' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-100/50'} 
      ${isChatActive ? 'bg-slate-100/80 border-slate-200 cursor-not-allowed' : ''}`}>
      <input {...getInputProps()} />
      <div className="p-6">
        <FileUp className="h-12 w-12 mx-auto text-slate-400 mb-4" />
        <p className={`font-semibold ${isChatActive ? 'text-slate-500' : 'text-slate-700'}`}>
          {isChatActive ? 'Dokumen Telah Dimuat' : 'Tarik & Lepas Dokumen Anda'}
        </p>
        <p className="text-sm text-slate-500 mt-1">
          {isChatActive ? uploadedFile?.name : 'atau klik untuk memilih file'}
        </p>
        {!isChatActive && <p className="text-xs text-slate-400 mt-4">Mendukung: PDF, DOCX, TXT</p>}
      </div>
    </div>
  );
};

export default FileUploader;