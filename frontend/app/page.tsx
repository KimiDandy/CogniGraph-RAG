"use client";

import { useState } from "react";
import FileUploader from "@/components/FileUploader";
import ChatInterface from "@/components/ChatInterface";

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  text_content?: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isChatActive, setIsChatActive] = useState(false);
  const [currentFilename, setCurrentFilename] = useState<string>("");
  const [textContent, setTextContent] = useState<string>("");

  const handleUploadComplete = (filename: string, text: string) => {
    setCurrentFilename(filename);
    setTextContent(text);
    setIsChatActive(true);
    setMessages([
      {
        role: 'assistant',
        content: `Dokumen "${filename}" telah berhasil dianalisis. Silakan ajukan pertanyaan Anda.`
      }
    ]);
  };

  const handleNewMessage = (message: Message) => {
    setMessages(prevMessages => [...prevMessages, message]);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 sm:p-6 lg:p-8">
      <header className="p-6 border-b border-gray-200 w-full max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center text-gray-800 tracking-tight">
          CogniGraph RAG
        </h1>
        <p className="text-center text-gray-500 mt-1">Your AI-Powered Document Analyst</p>
      </header>
      <main className="min-h-screen w-full p-4 sm:p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: Uploader */}
        <div className="lg:col-span-1 h-full">
          <div className="bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg border border-white/20 p-6 h-full flex flex-col">
            <header className="mb-6">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                CogniGraph RAG
              </h1>
              <p className="mt-1 text-sm text-slate-600">
                Analisis Dokumen Cerdas dengan Knowledge Graphs.
              </p>
            </header>
            <FileUploader
              onUploadComplete={handleUploadComplete}
              isChatActive={isChatActive}
            />
          </div>
        </div>

        {/* Right Panel: Chat Interface */}
        <div className="lg:col-span-2 h-full">
          <ChatInterface
            isChatActive={isChatActive}
            onNewMessage={handleNewMessage}
            messages={messages}
            filename={currentFilename}
            textContent={textContent}
          />
        </div>
      </main>
      <footer className="mt-8 text-center text-gray-500 text-sm">
        <p>&copy; {new Date().getFullYear()} CogniGraph RAG. Built with Next.js and FastAPI.</p>
      </footer>
    </div>
  );
}