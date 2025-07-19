"use client";

import { useState } from "react";
import FileUploader from "@/components/FileUploader";
import ChatInterface from "@/components/ChatInterface";
import DocumentLibrary from "@/components/DocumentLibrary";

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface Document {
  name: string;
  status: 'processing' | 'completed' | 'error';
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<Document[]>([]);
  const [activeFiles, setActiveFiles] = useState<string[]>([]);

  const handleNewMessage = (message: Message) => {
    setMessages(prevMessages => [...prevMessages, message]);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 sm:p-6 lg:p-8">
      <header className="p-6 border-b border-gray-200 w-full max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center text-gray-800 tracking-tight">
          CogniGraph RAG
        </h1>
        <p className="text-center text-gray-500 mt-1">Your Multi-Document AI Analyst</p>
      </header>
      <main className="min-h-screen w-full p-4 sm:p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: Uploader & Document Library */}
        <div className="lg:col-span-1 h-full flex flex-col gap-6">
          <div className="bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg border border-white/20 p-6">
             <header className="mb-6">
              <h2 className="text-xl font-bold text-slate-800 tracking-tight">
                1. Upload Dokumen
              </h2>
            </header>
            <FileUploader
              setUploadedFiles={setUploadedFiles}
            />
          </div>
          <div className="bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg border border-white/20 p-6 flex-grow">
            <header className="mb-6">
                <h2 className="text-xl font-bold text-slate-800 tracking-tight">
                    2. Pilih Dokumen Aktif
                </h2>
            </header>
            <DocumentLibrary 
              uploadedFiles={uploadedFiles}
              activeFiles={activeFiles}
              setActiveFiles={setActiveFiles}
            />
          </div>
        </div>

        {/* Right Panel: Chat Interface */}
        <div className="lg:col-span-2 h-full">
          <ChatInterface
            onNewMessage={handleNewMessage}
            messages={messages}
            activeFiles={activeFiles}
          />
        </div>
      </main>
      <footer className="mt-8 text-center text-gray-500 text-sm">
        <p>&copy; {new Date().getFullYear()} CogniGraph RAG. Built with Next.js and FastAPI.</p>
      </footer>
    </div>
  );
}