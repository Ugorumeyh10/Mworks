import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { fetchConversations, fetchMessages, sendMessage } from '../api/messages.js';
import { getToken } from '../api/session.js';
import './Messages.css';

export default function Messages() {
  const authed = Boolean(getToken());
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState('');
  const [thread, setThread] = useState([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const loadConvos = async (preferId) => {
    const rows = await fetchConversations();
    setConversations(rows);
    const nextId = preferId || activeId || rows[0]?.id || '';
    setActiveId(nextId);
    return nextId;
  };

  useEffect(() => {
    if (!authed) return undefined;
    loadConvos().catch(() => setConversations([]));
    return undefined;
  }, [authed]);

  useEffect(() => {
    if (!authed || !activeId) {
      setThread([]);
      return undefined;
    }
    let live = true;
    fetchMessages(activeId).then((rows) => {
      if (live) setThread(rows);
    }).catch(() => {
      if (live) setThread([]);
    });
    return () => { live = false; };
  }, [authed, activeId]);

  const active = conversations.find((c) => c.id === activeId);

  const send = async () => {
    if (!draft.trim() || !activeId) return;
    setBusy(true);
    setError('');
    try {
      const row = await sendMessage(activeId, draft.trim());
      setThread((m) => [...m, row]);
      setDraft('');
      await loadConvos(activeId);
    } catch (err) {
      setError(err.message || 'Could not send that message.');
    } finally {
      setBusy(false);
    }
  };

  if (!authed) {
    return (
      <div className="mk-page">
        <h1>Messages</h1>
        <div className="mk-empty"><Link to="/login?next=/messages">Sign in</Link> to read and send messages.</div>
      </div>
    );
  }

  return (
    <div className="messages-page">
      <div className="conv-list">
        <div className="conv-header">
          <h2>Messages</h2>
          <Icon name="search" className="sm" />
        </div>
        {conversations.length === 0 ? (
          <div className="mk-empty">No conversations yet.</div>
        ) : conversations.map((c) => (
          <button
            key={c.id}
            className={'conv-row' + (c.id === activeId ? ' active' : '')}
            onClick={() => setActiveId(c.id)}
          >
            <span className={`avatar sm${c.org ? ' org' : ''}`} style={c.steel ? { background: 'var(--steel)' } : undefined}>
              {c.avatar}
            </span>
            <div className="conv-text">
              <div className="conv-name">{c.name}</div>
              <div className="conv-preview">{c.preview}</div>
            </div>
            <div className="conv-meta">
              <span className="conv-time">{c.time}</span>
              {c.unread && <span className="unread-dot" />}
            </div>
          </button>
        ))}
      </div>

      <div className="conv-thread">
        {active ? (
          <>
            <div className="thread-header">
              <span className={`avatar${active.org ? ' org' : ''}`}>{active.avatar}</span>
              <strong>{active.name}</strong>
            </div>
            <div className="thread-body">
              <div className="thread-note">
                Negotiation, delivery updates, and interview scheduling stay on-platform so escrow and disputes have a full record.
              </div>
              {thread.map((m) => (
                <div className={m.fromMe ? 'bubble me' : 'bubble incoming'} key={m.id}>
                  {m.text}
                </div>
              ))}
            </div>
            {error && <p className="sf-err" role="alert">{error}</p>}
            <div className="thread-input">
              <textarea
                className="thread-field"
                rows="1"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder="Type a message..."
              />
              <button className="send-btn" onClick={send} disabled={busy || !draft.trim()} type="button">
                <Icon name="send" className="sm" />
              </button>
            </div>
          </>
        ) : (
          <div className="thread-body"><div className="mk-empty">Pick a conversation.</div></div>
        )}
      </div>
    </div>
  );
}
