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
    <div className="min-h-screen">
      <div className="container mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
        <header className="text-center mb-10">
          <h1 className="text-4xl font-bold tracking-tighter text-slate-800">
            CogniGraph RAG
          </h1>
          <p className="text-slate-600 mt-2">Analis AI Multi-Dokumen</p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-8 bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
          {/* Left Panel: Uploader & Document Library */}
          <div className="lg:col-span-1 flex flex-col gap-8">
            <div>
              <header className="mb-4">
                <h2 className="text-xl font-bold tracking-tight">
                  1. Unggah Dokumen
                </h2>
              </header>
              <FileUploader setUploadedFiles={setUploadedFiles} />
            </div>
            <div className="flex-grow flex flex-col">
              <header className="mb-4">
                <h2 className="text-xl font-bold tracking-tight">
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
          <div className="lg:col-span-2"> 
            <ChatInterface
              onNewMessage={handleNewMessage}
              messages={messages}
              activeFiles={activeFiles}
              uploadedFiles={uploadedFiles} 
            />
          </div>
        </main>

        <footer className="mt-12 text-center text-slate-500 text-sm">
          <p>© 2025 CogniGraph RAG. Built by Kimi Dandy Yudanarko.</p>
        </footer>
      </div>
    </div>
  );
}