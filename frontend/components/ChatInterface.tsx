"use client";

import * as React from 'react';

// Define the component's props interface
interface ChatInterfaceProps {
  isLoading: boolean;
  extractedText: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ isLoading, extractedText }) => {
  return (
    <div className="w-full h-96 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
      <div className="h-full overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500 dark:text-gray-400">Menganalisis dokumen...</p>
          </div>
        ) : extractedText ? (
          <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-sans">
            {extractedText}
          </pre>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400 dark:text-gray-500">Silakan upload dokumen untuk memulai.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatInterface;