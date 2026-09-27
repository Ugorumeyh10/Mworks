import { useEffect } from 'react';
import Icon from './Icon.jsx';
import './Popup.css';

export default function Popup({
  open,
  title,
  children,
  onClose,
  actions,
  size = 'md',
}) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="pop-root" role="presentation">
      <button type="button" className="pop-scrim" aria-label="Close dialog" onClick={onClose} />
      <div
        className={`pop-panel pop-${size}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'pop-title' : undefined}
      >
        <div className="pop-goldbar" aria-hidden="true" />
        {title && (
          <div className="pop-head">
            <h2 id="pop-title">{title}</h2>
            <button type="button" className="pop-x" onClick={onClose} aria-label="Close">
              <Icon name="x" />
            </button>
          </div>
        )}
        <div className="pop-body">{children}</div>
        {actions && <div className="pop-actions">{actions}</div>}
      </div>
    </div>
  );
}
