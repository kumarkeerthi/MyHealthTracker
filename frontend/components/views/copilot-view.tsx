'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Bot, Database, Send } from 'lucide-react';
import { getCopilotConversation, sendCopilotMessage } from '@/lib/api';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  dbAction?: boolean;
};

export function CopilotView() {
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [typingMessage, setTypingMessage] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typingMessage]);

  useEffect(() => {
    if (!conversationId) return;
    void getCopilotConversation(conversationId).then((detail) => {
      const loaded = detail.messages.map((msg, index) => ({
        id: `${conversationId}-${index}`,
        role: msg.role === 'assistant' ? 'assistant' : 'user',
        content: msg.content,
      }));
      setMessages(loaded);
    }).catch(() => undefined);
  }, [conversationId]);

  const canSend = useMemo(() => input.trim().length > 0 && !sending, [input, sending]);

  const runTypingAnimation = async (message: string, dbAction: boolean) => {
    setTypingMessage('');
    for (let i = 1; i <= message.length; i += 1) {
      setTypingMessage(message.slice(0, i));
      await new Promise((resolve) => setTimeout(resolve, 8));
    }
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: message, dbAction }]);
    setTypingMessage(null);
  };

  const sendMessage = async () => {
    if (!canSend) return;
    const content = input.trim();
    setInput('');
    setSending(true);
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content }]);

    try {
      const response = await sendCopilotMessage({ message: content, conversation_id: conversationId });
      setConversationId(response.conversation_id);
      const dbAction = response.actions_executed.some((action) => action.db_action);
      await runTypingAnimation(response.assistant_message, dbAction);
    } catch {
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: 'Copilot is unavailable. Please retry.' }]);
      setTypingMessage(null);
    } finally {
      setSending(false);
    }
  };

  return (
    <section className="glass-card flex h-[70vh] flex-col p-4">
      <header className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-slate-300">
        <Bot size={16} />
        Metabolic Copilot
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[82%] rounded-2xl px-3 py-2 text-sm ${message.role === 'user' ? 'bg-electric/40 text-white' : 'bg-white/10 text-slate-100'}`}>
              <p>{message.content}</p>
              {message.dbAction && (
                <div className="mt-2 inline-flex items-center gap-1 rounded-full border border-emerald-300/40 bg-emerald-400/10 px-2 py-1 text-[10px] uppercase tracking-[0.15em] text-emerald-200">
                  <Database size={11} /> DB action
                </div>
              )}
            </div>
          </div>
        ))}
        {typingMessage !== null && (
          <div className="flex justify-start">
            <div className="max-w-[82%] rounded-2xl bg-white/10 px-3 py-2 text-sm text-slate-200">{typingMessage}</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mt-3 flex items-center gap-2 border-t border-white/10 pt-3">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              void sendMessage();
            }
          }}
          placeholder="Ask about food, carbs, or log a meal..."
          className="flex-1 rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-white outline-none placeholder:text-slate-500"
        />
        <button
          type="button"
          onClick={() => void sendMessage()}
          disabled={!canSend}
          className="inline-flex items-center gap-1 rounded-xl bg-electric px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send size={12} /> Send
        </button>
      </div>
    </section>
  );
}
