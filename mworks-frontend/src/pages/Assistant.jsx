import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { fetchAssistantMessages, sendAssistantMessage } from '../api/assistant.js';
import { getToken } from '../api/session.js';
import './Assistant.css';

export default function Assistant() {
  const authed = Boolean(getToken());
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!authed) return undefined;
    fetchAssistantMessages().then(setMessages).catch(() => setMessages([]));
    return undefined;
  }, [authed]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    if (!draft.trim() || busy) return;
    const text = draft.trim();
    setDraft('');
    setBusy(true);
    try {
      const turns = await sendAssistantMessage(text);
      setMessages((m) => [...m, ...turns]);
    } catch {
      setMessages((m) => [
        ...m,
        { from: 'me', text },
        { from: 'bot', text: 'I could not reach the assistant just then. Try again in a moment.' },
      ]);
    } finally {
      setBusy(false);
    }
  };

  if (!authed) {
    return (
      <div className="mk-page">
        <h1>Mworks Assistant</h1>
        <div className="mk-empty"><Link to="/login?next=/assistant">Sign in</Link> to ask about your listings, orders, and applications.</div>
      </div>
    );
  }

  return (
    <div className="assistant-page">
      <div className="assistant-header">
        <Icon name="bot" className="lg" />
        <div>
          <h2>Mworks Assistant</h2>
          <p>Answers from your listings, orders, and applications. Falls back to account rules if the model is down.</p>
        </div>
      </div>

      <div className="chat-thread">
        {messages.map((m, i) =>
          m.from === 'bot' ? (
            <div className="botrow" key={i}>
              <div className="bicon"><Icon name="bot" className="sm" /></div>
              <div className="bubble bot">{m.text}</div>
            </div>
          ) : (
            <div className="bubble me" key={i}>{m.text}</div>
          )
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask about your listings, jobs, or an order..."
        />
        <button className="send-btn" onClick={send} disabled={busy}><Icon name="send" className="sm" /></button>
      </div>
    </div>
  );
}
