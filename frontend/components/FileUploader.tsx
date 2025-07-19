"use client";

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFile } from '@/lib/api';
import { FileUp } from 'lucide-react';
import { Document } from '@/app/page';

interface FileUploaderProps {
  setUploadedFiles: React.Dispatch<React.SetStateAction<Document[]>>;
}

type UploadResult = { 
  name: string; 
  status: 'completed' | 'error'; 
  error?: any; 
};

const FileUploader: React.FC<FileUploaderProps> = ({ setUploadedFiles }) => {
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setIsUploading(true);

    // Add all new files to the list with 'processing' status immediately
    const newFiles: Document[] = acceptedFiles.map(file => ({ name: file.name, status: 'processing' }));
    setUploadedFiles(prev => [...prev, ...newFiles]);

    // Create an array of upload promises
    const uploadPromises: Promise<UploadResult>[] = acceptedFiles.map(file => 
      uploadFile(file, () => {}).then(
        () => ({ name: file.name, status: 'completed' }),
        (error) => ({ name: file.name, status: 'error', error })
      )
    );

    // Wait for all uploads to settle
    const results = await Promise.allSettled(uploadPromises);

    // Update statuses based on results
    setUploadedFiles(prev => {
      const newFileStates = [...prev];
      results.forEach(result => {
        if (result.status === 'fulfilled') {
          const { name, status, error } = result.value;
          if (status === 'error' && error) {
            console.error(`Upload error for ${name}:`, error);
          }
          const fileIndex = newFileStates.findIndex(f => f.name === name && f.status === 'processing');
          if (fileIndex !== -1) {
            newFileStates[fileIndex] = { ...newFileStates[fileIndex], status };
          }
        }
      });
      return newFileStates;
    });

    setIsUploading(false);
  }, [setUploadedFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop: handleUpload,
    disabled: isUploading,
    multiple: true,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    }
  });

  return (
    <div {...getRootProps()} className={`w-full h-full border-2 border-dashed rounded-xl flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 
      ${isDragActive ? 'border-blue-500 bg-blue-100/50' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-100/50'} 
      ${isUploading ? 'bg-slate-100/80 border-slate-200 cursor-wait' : ''}`}>
      <input {...getInputProps()} />
      <div className="p-6">
        <FileUp className="h-12 w-12 mx-auto text-slate-400 mb-4" />
        <p className={`font-semibold ${isUploading ? 'text-slate-500' : 'text-slate-700'}`}>
          {isUploading ? 'Sedang Mengunggah...' : 'Tarik & Lepas Dokumen'}
        </p>
        <p className="text-sm text-slate-500 mt-1">
          {isUploading ? 'Harap tunggu' : 'atau klik untuk memilih file'}
        </p>
        {!isUploading && <p className="text-xs text-slate-400 mt-4">Mendukung: PDF, DOCX, TXT</p>}
      </div>
    </div>
  );
};

export default FileUploader;