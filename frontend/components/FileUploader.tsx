"use client";

import * as React from 'react';
import { useState } from 'react';
import { uploadAndParseFile } from "@/lib/api";

// Define the component's props interface
interface FileUploaderProps {
  setIsLoading: (isLoading: boolean) => void;
  setExtractedText: (text: string) => void;
}

const FileUploader: React.FC<FileUploaderProps> = ({ setIsLoading, setExtractedText }) => {
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsLoading(true);
    setExtractedText("");

    try {
      const result = await uploadAndParseFile(file);
      setExtractedText(result.message || "File processed, but no confirmation message received.");
    } catch (error) {
      console.error("Upload failed:", error);
      setExtractedText("Error: Failed to upload or parse the file.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg text-center">
      <input
        type="file"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-500
          file:mr-4 file:py-2 file:px-4
          file:rounded-full file:border-0
          file:text-sm file:font-semibold
          file:bg-violet-50 file:text-violet-700
          hover:file:bg-violet-100"
        accept=".pdf, .docx, .pptx, .txt"
      />
    </div>
  );
}

export default FileUploader;