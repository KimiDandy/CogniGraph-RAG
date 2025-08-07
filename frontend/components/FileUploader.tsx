"use client";

import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
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

    const uploadPromises = acceptedFiles.map(file => 
      uploadFile(file, () => {}).then(
        () => ({ name: file.name, status: 'completed' as const }),
        (error) => ({ name: file.name, status: 'error' as const, error })
      )
    );

    toast.promise(
      Promise.allSettled(uploadPromises).then(results => {
        let hasError = false;
        setUploadedFiles(prev => {
          const newFileStates = [...prev];
          results.forEach(result => {
            if (result.status === 'fulfilled') {
              const uploadResult = result.value;
              const fileIndex = newFileStates.findIndex(f => f.name === uploadResult.name && f.status === 'processing');
              if (fileIndex !== -1) {
                if (uploadResult.status === 'error') {
                  hasError = true;
                  console.error(`Upload error for ${uploadResult.name}:`, uploadResult.error);
                  newFileStates[fileIndex].status = 'error';
                } else {
                  newFileStates[fileIndex].status = 'completed';
                }
              }
            } else {
              hasError = true;
              console.error('An upload promise was rejected:', result.reason);
            }
          });

          if (hasError) {
            // The error for the toast is thrown here, so the toast promise will catch it.
            throw new Error("Beberapa file gagal diunggah.");
          }
          return newFileStates;
        });
      }),
      {
        loading: 'Mengunggah file...',
        success: 'File berhasil diunggah!',
        error: (err) => err.message || 'Terjadi kesalahan saat mengunggah.',
      }
    );

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
    <div 
      {...getRootProps()} 
      className={`relative block w-full rounded-lg border-2 border-dashed p-8 text-center transition-all duration-300
        ${isDragActive ? 'border-indigo-600 bg-indigo-50' : 'border-gray-300'}
        ${isUploading ? 'cursor-wait bg-gray-100' : 'cursor-pointer hover:border-indigo-400'}
      `}
    >
      <input {...getInputProps()} />
      <FileUp className="mx-auto h-10 w-10 text-gray-400" />
      <span className="mt-2 block text-sm font-semibold text-indigo-600">
        {isUploading ? 'Mengunggah...' : 'Klik untuk mengunggah atau seret & lepas'}
      </span>
      <p className="mt-1 block text-xs text-gray-500">
        {isUploading ? 'Mohon tunggu...' : 'Mendukung PDF, DOCX, TXT'}
      </p>
    </div>
  );
};

export default FileUploader;