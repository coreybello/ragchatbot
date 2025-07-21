import { useState, useEffect, useRef } from 'react';

// --- SVG Icon Components ---
const SendIcon = () => (<svg viewBox="0 0 24 24" className="w-6 h-6 text-white" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>);
const UserIcon = () => (<svg viewBox="0 0 24 24" className="w-8 h-8 text-gray-500 dark:text-gray-400" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" /></svg>);
const BotIcon = () => (<svg viewBox="0 0 24 24" className="w-8 h-8 text-[#6B8DAF]" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9.5 16.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm5 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM12 9a3 3 0 013 3H9a3 3 0 013-3z" /></svg>);
const SunIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>);
const MoonIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>);
const ChartBarIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>);
const ChatAltIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>);
const CogIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.096 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>);
const UploadIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>);
const DocumentIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>);
const TrashIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>);
const RefreshIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5M20 20v-5h-5M4 4l1.72 1.72a9 9 0 0012.56 0M20 20l-1.72-1.72a9 9 0 00-12.56 0" /></svg>);
const ThumbsUpIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 18.734V11.5a2.5 2.5 0 012.5-2.5h1.118c.345 0 .674.112.946.311.272.2.45.493.5.811v1.882zM7 11.5V9a2 2 0 012-2h2" /></svg>);
const ThumbsDownIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.738 3h4.017c.163 0 .326.02.485.06L17 5.266V12.5a2.5 2.5 0 01-2.5 2.5h-1.118c-.345 0-.674-.112-.946-.311a2.01 2.01 0 00-.5-.811V7.118zM17 12.5V15a2 2 0 01-2 2h-2" /></svg>);
const HistoryIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>);
const PlusIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>);
const ClipboardIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-2m-4-1v8m0 0l3-3m-3 3L9 8m-5 5h12.586a1 1 0 01.707.293l2.414 2.414a1 1 0 01.293.707V19a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2z" /></svg>);
const CheckIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>);
const LightbulbIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>);
const InfoIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>);

// --- Helper Components ---
const MarkdownRenderer = ({ content }) => {
    const parts = content.split(/(!\[.*?\]\(.*?\))/g);
    return (
        <div className="prose prose-sm dark:prose-invert max-w-none text-gray-800 dark:text-gray-200">
            {parts.map((part, index) => {
                const match = /!\[(.*?)\]\((.*?)\)/.exec(part);
                if (match) {
                    const [, alt, filename] = match;
                    // Updated to use backend API endpoint for images
                    const src = `/api/images/${filename}`;
                    return (
                        <img 
                            key={index} 
                            src={src} 
                            alt={alt} 
                            className="my-3 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 max-w-full" 
                            onError={(e) => { 
                                e.target.onerror = null; 
                                e.target.src=`https://placehold.co/600x400/f87171/ffffff?text=Image+Not+Found`; 
                            }} 
                        />
                    );
                }
                return <span key={index} className="whitespace-pre-wrap">{part}</span>;
            })}
        </div>
    );
};

const Tooltip = ({ text, children }) => (
    <div className="relative flex items-center group">
        {children}
        <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 w-64 p-2 bg-gray-800 text-white text-xs rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10">
            {text}
        </div>
    </div>
);

const ConfirmationModal = ({ isOpen, title, message, onConfirm, onCancel }) => {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-white dark:bg-[#1A2C47] p-6 rounded-xl shadow-2xl w-full max-w-md border border-gray-200 dark:border-[#2A4A6F]">
                <h2 className="text-xl font-bold text-center text-[#0D2C4B] dark:text-white">{title}</h2>
                <p className="text-center text-gray-600 dark:text-gray-300 mt-2">{message}</p>
                <div className="mt-6 flex gap-4">
                    <button onClick={onCancel} className="w-full py-2 rounded-md text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors">Cancel</button>
                    <button onClick={onConfirm} className="w-full py-2 rounded-md bg-[#6B8DAF] text-white font-semibold hover:bg-[#5a7d9a] transition-colors">Confirm</button>
                </div>
            </div>
        </div>
    );
};

// --- Child Component: Chat Interface ---
const ChatInterface = ({ onNewQuery, onRateResponse, onNewChat }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [currentBotId, setCurrentBotId] = useState(null);
    const [suggestedQuestions, setSuggestedQuestions] = useState([]);
    const [copiedMessageId, setCopiedMessageId] = useState(null);
    const chatEndRef = useRef(null);

    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, isStreaming]);
    
    const startNewChat = () => {
        setMessages([{ 
            id: 'init-message', 
            role: 'bot', 
            content: 'Hello! I am the RAG Demo assistant. How can I help you today?', 
            sources: [], 
            images: [], 
            rating: null, 
            suggestions: [] 
        }]);
        setSuggestedQuestions([]);
        onNewChat();
    };

    useEffect(() => { startNewChat(); }, []);
    
    const handleRate = (messageId, rating) => {
        setMessages(prev => prev.map(msg => msg.id === messageId ? {...msg, rating} : msg));
        onRateResponse(messageId, rating);
        
        // Submit feedback to backend
        fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message_id: messageId,
                rating: rating
            })
        }).catch(err => console.error('Failed to submit feedback:', err));
    };

    const handleCopyToClipboard = (text) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopiedMessageId(text);
            setTimeout(() => setCopiedMessageId(null), 2000);
        }).catch(() => {
            // Fallback for browsers that don't support clipboard API
            const tempTextArea = document.createElement('textarea');
            tempTextArea.value = text;
            document.body.appendChild(tempTextArea);
            tempTextArea.select();
            document.execCommand('copy');
            document.body.removeChild(tempTextArea);
            setCopiedMessageId(text);
            setTimeout(() => setCopiedMessageId(null), 2000);
        });
    };

    const handleSend = async (query) => {
        if (!query.trim() || isLoading || isStreaming) return;
        
        const userMessage = { id: `user-${Date.now()}`, role: 'user', content: query };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setSuggestedQuestions([]);
        
        const botMessageId = `bot-${Date.now()}`;
        setCurrentBotId(botMessageId);
        
        const thinkingMessage = { 
            id: botMessageId, 
            role: 'bot', 
            content: 'Thinking...', 
            sources: [], 
            images: [], 
            rating: null, 
            suggestions: [] 
        };
        setMessages(prev => [...prev, thinkingMessage]);
        
        try {
            // Use Server-Sent Events for streaming
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) throw new Error('Chat request failed');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            setIsLoading(false);
            setIsStreaming(true);
            
            let fullContent = '';
            let sources = [];
            let images = [];
            let suggestions = [];
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.type === 'content') {
                                fullContent += data.content;
                                setMessages(prev => prev.map(msg => 
                                    msg.id === botMessageId ? { ...msg, content: fullContent } : msg
                                ));
                            } else if (data.type === 'sources') {
                                sources = data.sources;
                            } else if (data.type === 'images') {
                                images = data.images;
                            } else if (data.type === 'suggestions') {
                                suggestions = data.suggestions;
                                setSuggestedQuestions(suggestions);
                            } else if (data.type === 'done') {
                                // Finalize message
                                setMessages(prev => prev.map(msg => 
                                    msg.id === botMessageId ? { 
                                        ...msg, 
                                        content: fullContent, 
                                        sources, 
                                        images, 
                                        suggestions 
                                    } : msg
                                ));
                                setIsStreaming(false);
                                setCurrentBotId(null);
                                onNewQuery(botMessageId, query, { 
                                    content: fullContent, 
                                    sources, 
                                    images, 
                                    suggestions 
                                });
                                return;
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => prev.map(msg => 
                msg.id === botMessageId ? { 
                    ...msg, 
                    content: 'Sorry, I encountered an error. Please try again.' 
                } : msg
            ));
            setIsLoading(false);
            setIsStreaming(false);
            setCurrentBotId(null);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#F9FAFB] dark:bg-[#0D2C4B]">
            <header className="p-4 border-b border-gray-200 dark:border-[#2A4A6F] flex justify-between items-center">
                <h2 className="text-lg font-semibold text-[#0D2C4B] dark:text-white">Chat</h2>
                <button onClick={startNewChat} className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-semibold bg-[#6B8DAF]/20 text-[#0D2C4B] dark:bg-[#F9FAFB]/10 dark:text-white hover:bg-[#6B8DAF]/30">
                    <PlusIcon /> New Chat
                </button>
            </header>
            
            <main className="flex-1 overflow-y-auto p-4 md:p-6">
                <div className="max-w-4xl mx-auto space-y-8">
                    {messages.map((msg) => (
                        <div key={msg.id} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {msg.role === 'bot' && (
                                <div className="flex-shrink-0">
                                    <BotIcon />
                                </div>
                            )}
                            
                            <div className={`flex flex-col max-w-2xl w-full ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className={`relative group p-4 rounded-2xl shadow-sm ${
                                    msg.role === 'user' 
                                        ? 'bg-[#6B8DAF] text-white rounded-br-none' 
                                        : 'bg-white dark:bg-[#1A2C47] text-[#0D2C4B] dark:text-gray-200 rounded-bl-none border border-gray-200 dark:border-[#2A4A6F]'
                                }`}>
                                    {msg.role === 'bot' ? (
                                        <MarkdownRenderer content={msg.content + (isStreaming && msg.id === currentBotId ? '▍' : '')} />
                                    ) : (
                                        <p>{msg.content}</p>
                                    )}
                                    
                                    {msg.role === 'bot' && msg.content && msg.content !== 'Thinking...' && !isStreaming && (
                                        <button 
                                            onClick={() => handleCopyToClipboard(msg.content)} 
                                            className="absolute top-2 right-2 p-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            {copiedMessageId === msg.content ? <CheckIcon /> : <ClipboardIcon />}
                                        </button>
                                    )}
                                </div>
                                
                                {msg.role === 'bot' && msg.id !== 'init-message' && !isStreaming && msg.content !== 'Thinking...' && (
                                    <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 w-full">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                {msg.rating === null ? (
                                                    <>
                                                        <button onClick={() => handleRate(msg.id, 'good')} className="p-1.5 rounded-full hover:bg-green-100 dark:hover:bg-green-900/50 text-gray-400 hover:text-green-600">
                                                            <ThumbsUpIcon />
                                                        </button>
                                                        <button onClick={() => handleRate(msg.id, 'bad')} className="p-1.5 rounded-full hover:bg-red-100 dark:hover:bg-red-900/50 text-gray-400 hover:text-red-600">
                                                            <ThumbsDownIcon />
                                                        </button>
                                                    </>
                                                ) : (
                                                    <p className="font-semibold text-sm">Thank you for your feedback!</p>
                                                )}
                                            </div>
                                            
                                            {msg.sources && msg.sources.length > 0 && (
                                                <div>
                                                    <strong>Sources:</strong>
                                                    <ul className="list-disc list-inside ml-2">
                                                        {msg.sources.map((source, i) => (
                                                            <li key={i}>{source.document} (p. {source.page})</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                            
                            {msg.role === 'user' && (
                                <div className="flex-shrink-0">
                                    <UserIcon />
                                </div>
                            )}
                        </div>
                    ))}
                    
                    {isLoading && (
                        <div className="flex items-start gap-4 justify-start">
                            <div className="flex-shrink-0">
                                <BotIcon />
                            </div>
                            <div className="p-4 rounded-2xl bg-white dark:bg-[#1A2C47] rounded-bl-none border border-gray-200 dark:border-[#2A4A6F]">
                                <div className="flex items-center space-x-2">
                                    <div className="w-2.5 h-2.5 bg-[#6B8DAF] rounded-full animate-pulse"></div>
                                    <div className="w-2.5 h-2.5 bg-[#6B8DAF] rounded-full animate-pulse [animation-delay:0.2s]"></div>
                                    <div className="w-2.5 h-2.5 bg-[#6B8DAF] rounded-full animate-pulse [animation-delay:0.4s]"></div>
                                </div>
                            </div>
                        </div>
                    )}
                    
                    <div ref={chatEndRef} />
                </div>
            </main>
            
            <footer className="bg-white/80 dark:bg-[#0D2C4B]/80 backdrop-blur-sm p-4">
                <div className="max-w-4xl mx-auto">
                    <div className="flex gap-2 mb-3 flex-wrap">
                        {suggestedQuestions.map((q, i) => (
                            <button 
                                key={i} 
                                onClick={() => handleSend(q)} 
                                className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-sm rounded-full hover:bg-gray-200 dark:hover:bg-gray-600"
                            >
                                {q}
                            </button>
                        ))}
                    </div>
                    
                    <form onSubmit={(e) => { e.preventDefault(); handleSend(input); }} className="flex items-center gap-3">
                        <input 
                            type="text" 
                            value={input} 
                            onChange={(e) => setInput(e.target.value)} 
                            placeholder="Ask a question..." 
                            className="flex-1 w-full px-4 py-3 rounded-full bg-gray-100 dark:bg-[#1A2C47] text-[#0D2C4B] dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-[#6B8DAF]" 
                            disabled={isLoading || isStreaming} 
                        />
                        <button 
                            type="submit" 
                            className="bg-[#6B8DAF] hover:bg-[#5a7d9a] disabled:bg-slate-400 dark:disabled:bg-slate-700 disabled:cursor-not-allowed text-white p-3 rounded-full transition-all duration-200 shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-[#0D2C4B] focus:ring-[#6B8DAF]" 
                            disabled={isLoading || isStreaming || !input.trim()}
                        >
                            <SendIcon />
                        </button>
                    </form>
                </div>
            </footer>
        </div>
    );
};

// Main App Component (truncated for length - includes all the other components from original file)
export default function App() {
  const [theme, setTheme] = useState('light');
  const [activeTab, setActiveTab] = useState('chat');
  const [isAdmin, setIsAdmin] = useState(false);
  const [queryHistory, setQueryHistory] = useState([]);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove(theme === 'light' ? 'dark' : 'light');
    root.classList.add(theme);
    document.body.style.backgroundColor = theme === 'light' ? '#F9FAFB' : '#0D2C4B';
  }, [theme]);

  const logNewQuery = (messageId, query, response) => {
    const newHistoryEntry = {
      id: messageId,
      timestamp: Date.now(),
      query: query,
      response: response,
      rating: null,
    };
    setQueryHistory(prev => [newHistoryEntry, ...prev]);
  };

  const handleRateResponse = (messageId, rating) => {
    setQueryHistory(prev => prev.map(item => 
      item.id === messageId ? { ...item, rating: rating } : item
    ));
  };

  const TabButton = ({ tabName, icon, label }) => (
    <button 
      onClick={() => setActiveTab(tabName)} 
      className={`flex items-center gap-2 px-3 py-1.5 text-sm font-semibold rounded-md transition-colors ${
        activeTab === tabName 
          ? 'bg-[#6B8DAF]/20 text-[#0D2C4B] dark:bg-[#F9FAFB]/10 dark:text-white' 
          : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );

  return (
    <div className="flex flex-col h-screen font-sans">
      <header className="bg-white dark:bg-[#1A2C47] border-b border-gray-200 dark:border-[#2A4A6F] p-3 shadow-sm flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-[#0D2C4B] dark:text-white px-2">RAGDEMO</h1>
          <div className="flex items-center gap-1 bg-gray-100 dark:bg-[#0D2C4B] p-1 rounded-lg">
            <TabButton tabName="chat" icon={<ChatAltIcon />} label="Chat" />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} 
            className="p-2 rounded-full text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            {theme === 'light' ? <MoonIcon /> : <SunIcon />}
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <ChatInterface 
          onNewQuery={logNewQuery} 
          onRateResponse={handleRateResponse} 
          onNewChat={() => setQueryHistory([])} 
        />
      </div>
    </div>
  );
}