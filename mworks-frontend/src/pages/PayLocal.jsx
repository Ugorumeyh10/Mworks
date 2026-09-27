import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { money } from '../data/marketplace.js';
import { confirmLocalPayment, fetchOrder } from '../api/orders.js';
import { getToken } from '../api/session.js';
import './Checkout.css';

export default function PayLocal() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      navigate(`/login?next=${encodeURIComponent(`/checkout/pay/${id}`)}`);
      return undefined;
    }
    let live = true;
    fetchOrder(id)
      .then((row) => {
        if (live) setOrder(row);
      })
      .catch((err) => {
        if (live) setError(err.message || 'Order not found.');
      });
    return () => {
      live = false;
    };
  }, [id, navigate]);

  const pay = async () => {
    setBusy(true);
    setError('');
    try {
      const paid = await confirmLocalPayment(id);
      navigate(`/orders/${paid.id}`);
    } catch (err) {
      setError(err.message || 'Payment could not be completed.');
      setBusy(false);
    }
  };

  if (error && !order) {
    return (
      <div className="mk-page mk-narrow">
        <div className="mk-empty">{error}</div>
        <Link to="/browse" className="mk-btn ghost">Back to marketplace</Link>
      </div>
    );
  }

  if (!order) return <p className="body-text">Loading payment…</p>;

  if (order.state !== 'pending_payment') {
    return (
      <div className="mk-page mk-narrow">
        <div className="co-done">
          <h1>This order is already paid</h1>
          <Link to={`/orders/${order.id}`} className="mk-btn">Open order</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mk-page mk-narrow">
      <div className="mk-head">
        <div>
          <h1>Test escrow payment</h1>
          <p className="sub">
            Paystack test keys are not set, so this local confirm stands in for a Paystack success webhook.
            No card is charged.
          </p>
        </div>
      </div>
      <div className="mk-card">
        <div className="mk-sec-title">Order {order.id}</div>
        <p><strong>{order.title}</strong></p>
        <p>Amount to hold in escrow: <b>{money(order.amount)}</b></p>
        {error && <p className="co-err">{error}</p>}
        <button type="button" className="mk-btn" onClick={pay} disabled={busy}>
          <Icon name="lock" className="sm" />
          {busy ? 'Holding funds…' : `Pay ${money(order.amount)} (test)`}
        </button>
      </div>
    </div>
  );
}
