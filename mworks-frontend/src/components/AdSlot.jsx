import { useEffect, useRef } from 'react';

// Google AdSense slot. Set VITE_ADSENSE_CLIENT (ca-pub-...) to serve real ads;
// without it, a quiet placeholder keeps the layout honest in development.
const CLIENT = import.meta.env.VITE_ADSENSE_CLIENT || '';
let loaderInjected = false;

function injectLoader() {
  if (loaderInjected || !CLIENT) return;
  loaderInjected = true;
  const s = document.createElement('script');
  s.async = true;
  s.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${CLIENT}`;
  s.crossOrigin = 'anonymous';
  document.head.appendChild(s);
}

export default function AdSlot({ slot = '', format = 'auto', className = '' }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!CLIENT) return;
    injectLoader();
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      // Ad blockers throw here; the page should not care.
    }
  }, []);

  if (!CLIENT) {
    return (
      <div className={`ad-slot ad-slot-placeholder ${className}`} aria-hidden="true">
        <span>Ad</span>
      </div>
    );
  }

  return (
    <div className={`ad-slot ${className}`}>
      <ins
        ref={ref}
        className="adsbygoogle"
        style={{ display: 'block' }}
        data-ad-client={CLIENT}
        data-ad-slot={slot || undefined}
        data-ad-format={format}
        data-full-width-responsive="true"
      />
    </div>
  );
}
