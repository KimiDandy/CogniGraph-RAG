"use client";

import * as React from 'react';
import { useState } from 'react';
import { postQuery } from '@/lib/api';

// Define the component's props interface
interface ChatInterfaceProps {
  isLoading: boolean;
  setIsLoading: (isLoading: boolean) => void;
  extractedText: string;
  setExtractedText: (text: string) => void;
  activeFilename: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ isLoading, setIsLoading, extractedText, setExtractedText, activeFilename }) => {
  const [currentQuery, setCurrentQuery] = useState("");

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentQuery.trim()) return; // Don't send empty queries

    setIsLoading(true);
    // Clear previous answer while loading new one
    setExtractedText(""); 
    try {
      const result = await postQuery(currentQuery, activeFilename);
      setExtractedText(result.answer);
    } catch (error) {
      console.error("Query failed:", error);
      setExtractedText("Error: Failed to get an answer from the backend.");
    } finally {
      setCurrentQuery("");
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full h-96 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm flex flex-col">
      <div className="flex-grow overflow-y-auto p-4">
        {isLoading && !extractedText ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500 dark:text-gray-400">Mencari jawaban...</p>
          </div>
        ) : extractedText ? (
          <div className="prose dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap">{extractedText}</pre>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400 dark:text-gray-500">Silakan upload dokumen dan ajukan pertanyaan.</p>
          </div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 dark:border-gray-700 mt-auto">
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={currentQuery}
            onChange={(e) => setCurrentQuery(e.target.value)}
            placeholder="Tanyakan sesuatu tentang dokumen Anda..."
            className="flex-grow p-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="px-4 py-2 bg-violet-600 text-white rounded-md hover:bg-violet-700 disabled:bg-violet-300"
            disabled={isLoading || !currentQuery.trim()}
          >
            {isLoading ? '...' : 'Kirim'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatInterface;