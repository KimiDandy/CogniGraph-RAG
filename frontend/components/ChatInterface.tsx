"use client";

import { useState, useEffect, useRef } from 'react';
import { postQuery } from '@/lib/api';
import { Message } from '../app/page';
import { Send, User, Bot, Loader2, MessageSquare } from 'lucide-react';

interface ChatInterfaceProps {
  messages: Message[];
  onNewMessage: (message: Message) => void;
  filename: string;
  isChatActive: boolean;
  textContent: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  messages, 
  onNewMessage, 
  filename, 
  isChatActive, 
  textContent 
}) => {
  const [currentQuery, setCurrentQuery] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentQuery.trim() || !isChatActive) return;

    const userMessage: Message = { role: 'user', content: currentQuery };
    onNewMessage(userMessage);
    setCurrentQuery("");
    setIsQuerying(true);

    try {
      // Pass the previous messages for context/history
      const result = await postQuery(currentQuery, filename, messages, textContent);
      const assistantMessage: Message = { role: 'assistant', content: result.answer };
      onNewMessage(assistantMessage);
    } catch (error) {
      console.error("Query failed:", error);
      const errorMessage: Message = { role: 'assistant', content: "Maaf, terjadi kesalahan saat menjawab pertanyaan Anda." };
      onNewMessage(errorMessage);
    } finally {
      setIsQuerying(false);
    }
  };

  const isDisabled = !isChatActive || isQuerying;

  return (
    <div className="bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg border border-white/20 h-full flex flex-col">
      <div ref={chatContainerRef} className="flex-grow p-4 sm:p-6 space-y-6 overflow-y-auto">
        {messages.length === 0 && !isChatActive ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-500">
            <MessageSquare size={48} className="mb-4"/>
            <h2 className="text-xl font-semibold text-slate-700">Selamat Datang di CogniGraph</h2>
            <p>Unggah dokumen di panel kiri untuk memulai analisis dan percakapan cerdas Anda.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`flex items-start gap-3 w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center flex-shrink-0">
                  <Bot size={20} />
                </div>
              )}
              <div className={`px-4 py-3 rounded-2xl max-w-md md:max-w-lg lg:max-w-2xl shadow-sm ${message.role === 'user' ? 'bg-blue-500 text-white rounded-br-none' : 'bg-white text-slate-800 rounded-bl-none'}`}>
                <p className="whitespace-pre-wrap text-sm sm:text-base">{message.content}</p>
              </div>
              {message.role === 'user' && (
                 <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center flex-shrink-0">
                  <User size={20} />
                </div>
              )}
            </div>
          ))
        )}
         {isQuerying && (
            <div className="flex items-start gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center flex-shrink-0"><Bot size={20} /></div>
                <div className="px-4 py-3 rounded-2xl max-w-md bg-white text-slate-800 rounded-bl-none shadow-sm flex items-center space-x-2">
                    <Loader2 className="h-5 w-5 text-slate-500 animate-spin"/>
                    <span className="text-sm text-slate-500">Thinking...</span>
                </div>
            </div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="p-3 sm:p-4 border-t border-white/20">
        <div className="relative">
          <input
            type="text"
            value={currentQuery}
            onChange={(e) => setCurrentQuery(e.target.value)}
            placeholder={!isChatActive ? 'Unggah dokumen untuk memulai...' : 'Ketik pertanyaan Anda...'}
            className="w-full py-3 pl-4 pr-14 text-slate-800 bg-white/80 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-300 disabled:bg-slate-200/50"
            disabled={isDisabled}
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-blue-500 text-white hover:bg-blue-600 disabled:bg-slate-400 disabled:cursor-not-allowed transition-all duration-300"
            disabled={isDisabled || !currentQuery.trim()}
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatInterface;