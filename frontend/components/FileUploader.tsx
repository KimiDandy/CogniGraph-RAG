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
        {isUploading ? 'Uploading...' : 'Click to upload or drag & drop'}
      </span>
      <p className="mt-1 block text-xs text-gray-500">
        {isUploading ? 'Please wait...' : 'PDF, DOCX, PPTX, TXT'}
      </p>
    </div>
  );
};

export default FileUploader;