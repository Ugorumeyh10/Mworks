import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { money, commissionRate, STATE_LABEL, STATE_TONE } from '../data/marketplace.js';
import { confirmDelivery, fetchOrder, fetchOrderContent, fetchOrderDownload, verifyPayment } from '../api/orders.js';
import { getToken } from '../api/session.js';
import './Orders.css';

function steps(kind, state) {
  const labels = kind === 'hire' || kind === 'revise'
    ? ['Brief sent', 'Escrow funded', 'Work delivered', 'You accepted - funds released']
    : ['Payment held in escrow', 'Seller delivered', 'You confirmed delivery', 'Funds released to seller'];
  const reached = {
    pending_payment: 1,
    in_progress: 2,
    funds_held: 1,
    delivered: 2,
    completed: 4,
    disputed: 2,
  }[state] ?? 1;
  return labels.map((label, i) => ({
    label,
    status: i + 1 < reached ? 'done' : i + 1 === reached ? 'active' : 'todo',
  }));
}

export default function OrderDetail() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [dlBusy, setDlBusy] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      navigate(`/login?next=${encodeURIComponent(`/orders/${id}`)}`);
      return undefined;
    }
    let live = true;
    const load = params.get('paid') === '1' ? verifyPayment(id).catch(() => fetchOrder(id)) : fetchOrder(id);
    load
      .then((row) => {
        if (live) setOrder(row);
      })
      .catch((err) => {
        if (live) setError(err.message || 'Order not found.');
      });
    return () => {
      live = false;
    };
  }, [id, navigate, params]);

  useEffect(() => {
    if (!order?.hasPrompt) return undefined;
    let live = true;
    fetchOrderContent(order.id)
      .then((data) => {
        if (live) setPrompt(data.promptText || '');
      })
      .catch(() => {
        if (live) setPrompt('');
      });
    return () => {
      live = false;
    };
  }, [order]);

  if (error) {
    return (
      <div className="mk-page mk-narrow">
        <Link to="/orders" className="mk-back"><Icon name="arrow-left" className="sm" /> My orders</Link>
        <div className="mk-empty">{error}</div>
      </div>
    );
  }

  if (!order) return <p className="body-text">Loading order…</p>;

  const state = order.state;
  const rate = commissionRate(order.type);
  const sellerGets = order.amount * (1 - rate);
  const flow = steps(order.kind, state);
  const disputed = state === 'disputed';

  const copyPrompt = async () => {
    if (!prompt) return;
    try {
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setError('Could not copy the prompt.');
    }
  };

  const download = async () => {
    setDlBusy(true);
    try {
      const data = await fetchOrderDownload(order.id);
      window.location.assign(data.url);
    } catch (err) {
      setError(err.message || 'Download is not available yet.');
    } finally {
      setDlBusy(false);
    }
  };

  const confirm = async () => {
    setBusy(true);
    try {
      const next = await confirmDelivery(order.id);
      setOrder(next);
    } catch (err) {
      setError(err.message || 'Could not confirm delivery.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mk-page mk-narrow">
      <Link to="/orders" className="mk-back"><Icon name="arrow-left" className="sm" /> My orders</Link>

      <div className="od-head">
        <div>
          <h1>{order.title}</h1>
          <span className="od-sub">
            {order.kind === 'revise' ? 'Revise' : order.kind === 'hire' ? 'Customization hire' : 'Purchase'}
            {' · '}{order.id} · {order.placedAt}
          </span>
        </div>
        <span className={`mk-pill ${STATE_TONE[state] || 'info'}`}>{STATE_LABEL[state] || state}</span>
      </div>

      {order.brief && (
        <div className="mk-card od-brief">
          <div className="mk-sec-title">Your brief</div>
          <p>{order.brief}</p>
        </div>
      )}

      <div className="mk-card">
        <div className="mk-sec-title">Escrow status</div>
        <ol className={'od-steps' + (disputed ? ' has-dispute' : '')}>
          {flow.map((s, i) => (
            <li key={i} className={`od-step ${s.status}`}>
              <span className="od-dot">{s.status === 'done' ? <Icon name="check-circle" className="sm" /> : i + 1}</span>
              <span className="od-step-label">{s.label}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="mk-card">
        <div className="mk-sec-title">Activity</div>
        <ul className="od-timeline">
          {(order.timeline || []).map((t, i) => (
            <li key={i}>
              <span className="od-t">{t.t}</span>
              <span>{t.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mk-card od-amounts">
        <div className="od-amount-row"><span>{order.kind === 'hire' ? 'Funded to escrow' : 'You paid'}</span><b>{money(order.amount)}</b></div>
        <div className="od-amount-row muted"><span>Mworks commission ({Math.round(rate * 100)}%)</span><span>−{money(order.amount * rate)}</span></div>
        <div className="od-amount-row"><span>Seller receives on release</span><b>{money(sellerGets)}</b></div>
      </div>

      {state === 'pending_payment' && (
        <div className="mk-card od-actions">
          <p className="od-action-note">Payment is not complete. Finish checkout to move funds into escrow.</p>
          {order.paymentUrl && (
            <a className="mk-btn" href={order.paymentUrl}>Continue to payment</a>
          )}
        </div>
      )}

      {state === 'funds_held' && (
        <div className="mk-card od-actions">
          <p className="od-action-note">The seller is preparing your delivery. You can confirm once they have delivered.</p>
        </div>
      )}

      {order.hasPrompt && prompt && (
        <div className="mk-card od-prompt">
          <div className="mk-sec-title">{order.type === 'agent' ? 'Unlocked interviewer playbook' : 'Unlocked prompt'}</div>
          <pre className="od-prompt-body">{prompt}</pre>
          <button type="button" className="mk-btn ghost sm" onClick={copyPrompt}>
            {copied ? 'Copied' : 'Copy prompt'}
          </button>
        </div>
      )}

      {state === 'delivered' && (
        <div className="mk-card od-actions">
          <p className="od-action-note">
            <Icon name="shield" className="sm" />
            Check the delivery. Confirming releases {money(sellerGets)} to {order.counterparty?.name || 'the seller'}. This cannot be undone.
          </p>
          <div className="od-action-btns">
            {order.hasDownload && (
              <button type="button" className="mk-btn ghost" onClick={download} disabled={dlBusy}>
                {dlBusy ? 'Preparing file…' : 'Download pack'}
              </button>
            )}
            <button className="mk-btn" onClick={confirm} disabled={busy}>Confirm delivery and release funds</button>
          </div>
        </div>
      )}

      {state === 'completed' && (order.hasDownload || order.hasPrompt) && (
        <div className="mk-card od-actions">
          <p className="od-action-note">Your delivery stays available from this order.</p>
          {order.hasDownload && (
            <button type="button" className="mk-btn" onClick={download} disabled={dlBusy}>
              {dlBusy ? 'Preparing file…' : 'Download pack'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
