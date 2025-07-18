"use client";

import { useState } from "react";
import FileUploader from "@/components/FileUploader";
import ChatInterface from "@/components/ChatInterface";

export default function Page() {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [extractedText, setExtractedText] = useState<string>("");

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-2xl space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">
            CogniGraph RAG
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            Upload a document to start extracting information.
          </p>
        </div>

        <FileUploader
          setIsLoading={setIsLoading}
          setExtractedText={setExtractedText}
        />

        <ChatInterface isLoading={isLoading} extractedText={extractedText} />
      </div>
    </main>
  );
}