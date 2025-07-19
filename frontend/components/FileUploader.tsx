"use client";

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFile, checkStatus, StatusResponse } from '@/lib/api';
import { FileUp, Loader, XCircle } from 'lucide-react';

interface FileUploaderProps {
  onProcessingStart: (filename: string) => void;
  onProcessingComplete: (status: StatusResponse) => void;
  onProcessingError: (message: string) => void;
  isProcessing: boolean;
  error: string | null;
  currentFile: string;
}

const FileUploader: React.FC<FileUploaderProps> = ({ 
  onProcessingStart,
  onProcessingComplete,
  onProcessingError,
  isProcessing,
  error,
  currentFile
}) => {
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0 && !isProcessing) {
      const file = acceptedFiles[0];
      onProcessingStart(file.name);
      setProgress(0);
      setStatusMessage('Mengunggah file...');

      try {
        const uploadResponse = await uploadFile(file);
        const filename = uploadResponse.filename;
        setStatusMessage('Dokumen diterima, memulai analisis...');
        setProgress(25); // Initial progress after upload

        const pollStatus = async () => {
          try {
            const statusResponse = await checkStatus(filename);
            const newProgress = statusResponse.progress || progress;
            setProgress(newProgress);
            setStatusMessage(statusResponse.message || `Status: ${statusResponse.status}`);

            if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
              setProgress(100);
              onProcessingComplete(statusResponse);
            } else {
              setTimeout(pollStatus, 2000);
            }
          } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Gagal memeriksa status.';
            onProcessingError(errorMessage);
          }
        };
        setTimeout(pollStatus, 1000);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Gagal mengunggah file.';
        onProcessingError(errorMessage);
      }
    }
  }, [onProcessingStart, onProcessingComplete, onProcessingError, isProcessing, progress]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    disabled: isProcessing,
    multiple: false,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    }
  });

  // Display for processing or error state
  if (isProcessing || error) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-center p-4">
        <div className="mb-4">
          {error ? (
            <XCircle className="h-12 w-12 text-red-500" />
          ) : (
            <Loader className="h-12 w-12 text-blue-500 animate-spin" />
          )}
        </div>
        <p className="text-lg font-medium text-slate-800 break-all">{error ? 'Terjadi Kesalahan' : 'Sedang Menganalisis'}</p>
        <p className="text-sm text-slate-600 mb-4 break-all">{error ? error : currentFile}</p>
        {!error && (
            <div className="w-full bg-slate-200 rounded-full h-2.5">
                <div className="bg-blue-500 h-2.5 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
            </div>
        )}
        <p className="text-xs text-slate-500 mt-2">{statusMessage}</p>
      </div>
    );
  }

  // Default display for idle state
  return (
    <div {...getRootProps()} className={`w-full h-full border-2 border-dashed rounded-xl flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 
      ${isDragActive ? 'border-blue-500 bg-blue-100/50' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-100/50'}`}>
      <input {...getInputProps()} />
      <div className="p-6">
        <FileUp className="h-12 w-12 mx-auto text-slate-400 mb-4" />
        <p className="font-semibold text-slate-700">Tarik & Lepas Dokumen Anda</p>
        <p className="text-sm text-slate-500 mt-1">atau klik untuk memilih file</p>
        <p className="text-xs text-slate-400 mt-4">Mendukung: PDF, DOCX, TXT</p>
      </div>
    </div>
  );
};

export default FileUploader;