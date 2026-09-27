// Central icon set. Add a new <symbol id="i-name"> here, then use
// <Icon name="name" /> anywhere in the app. Kept as plain SVG (no
// external icon library) so the visual language stays exactly on-brand.
export default function IconSprite() {
  return (
    <svg style={{ display: 'none' }} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></symbol>
        <symbol id="i-bell" viewBox="0 0 24 24"><path d="M12 3a5 5 0 0 0-5 5v3.5c0 .7-.3 1.4-.8 1.9L5 15h14l-1.2-1.6c-.5-.5-.8-1.2-.8-1.9V8a5 5 0 0 0-5-5z" /><path d="M10 18a2 2 0 0 0 4 0" /></symbol>
        <symbol id="i-heart" viewBox="0 0 24 24"><path d="M12 20s-7-4.35-9.5-8.5C.7 8 2 4.5 5.5 4c2-.3 3.7.7 4.5 2.2C10.8 4.7 12.5 3.7 14.5 4 18 4.5 19.3 8 17.5 11.5 15 15.65 12 20 12 20z" /></symbol>
        <symbol id="i-message" viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 8.5 8.5 0 0 1-4-1L3 20l1-4.5A8.5 8.5 0 1 1 21 11.5z" /></symbol>
        <symbol id="i-share" viewBox="0 0 24 24"><circle cx="6" cy="12" r="2.2" /><circle cx="18" cy="6" r="2.2" /><circle cx="18" cy="18" r="2.2" /><line x1="8" y1="10.8" x2="16" y2="7.2" /><line x1="8" y1="13.2" x2="16" y2="16.8" /></symbol>
        <symbol id="i-home" viewBox="0 0 24 24"><path d="M4 11.5 12 4l8 7.5" /><path d="M6 10v9h12v-9" /><path d="M10 19v-5h4v5" /></symbol>
        <symbol id="i-briefcase" viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="11" rx="1.5" /><path d="M9 8V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" /><line x1="3" y1="13" x2="21" y2="13" /></symbol>
        <symbol id="i-plus" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></symbol>
        <symbol id="i-arrow-left" viewBox="0 0 24 24"><line x1="19" y1="12" x2="5" y2="12" /><polyline points="11 6 5 12 11 18" /></symbol>
        <symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.4" /><path d="M5 19c0-3.5 3-6 7-6s7 2.5 7 6" /></symbol>
        <symbol id="i-user-plus" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.2" /><path d="M3 19c0-3.2 2.7-5.5 6-5.5s6 2.3 6 5.5" /><line x1="18" y1="8" x2="18" y2="14" /><line x1="15" y1="11" x2="21" y2="11" /></symbol>
        <symbol id="i-check-circle" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><polyline points="7.5 12.5 10.5 15.5 16 9" /></symbol>
        <symbol id="i-star" viewBox="0 0 24 24"><polygon points="12 3 14.7 9.3 21.5 9.9 16.3 14.4 17.9 21 12 17.3 6.1 21 7.7 14.4 2.5 9.9 9.3 9.3" /></symbol>
        <symbol id="i-lock" viewBox="0 0 24 24"><rect x="4.5" y="10.5" width="15" height="10" rx="1.8" /><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" /></symbol>
        <symbol id="i-card" viewBox="0 0 24 24"><rect x="2.5" y="5.5" width="19" height="13" rx="2" /><line x1="2.5" y1="10" x2="21.5" y2="10" /></symbol>
        <symbol id="i-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><line x1="3" y1="12" x2="21" y2="12" /><path d="M12 3c3 3.2 3 14.8 0 18" /><path d="M12 3c-3 3.2-3 14.8 0 18" /></symbol>
        <symbol id="i-bot" viewBox="0 0 24 24"><rect x="5" y="8" width="14" height="10" rx="3" /><line x1="12" y1="4" x2="12" y2="8" /><circle cx="12" cy="3" r="1.1" fill="currentColor" stroke="none" /><circle cx="9" cy="13" r="1" fill="currentColor" stroke="none" /><circle cx="15" cy="13" r="1" fill="currentColor" stroke="none" /></symbol>
        <symbol id="i-send" viewBox="0 0 24 24"><path d="M21 3L3 10.5l7 2.5 2.5 7L21 3z" /></symbol>
        <symbol id="i-settings" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.2" /><path d="M19.4 13.5c.1-.5.1-1 0-1.5l1.8-1.4-2-3.4-2.1.6a7 7 0 0 0-1.3-.75L15.4 5h-4l-.4 2.05a7 7 0 0 0-1.3.75l-2.1-.6-2 3.4L7.4 12c-.1.5-.1 1 0 1.5l-1.8 1.4 2 3.4 2.1-.6c.4.3.85.55 1.3.75L11.4 21h4l.4-2.05a7 7 0 0 0 1.3-.75l2.1.6 2-3.4-1.8-1.4z" /></symbol>
        <symbol id="i-tag" viewBox="0 0 24 24"><path d="M4 4h7.5L20 12.5 12.5 20 4 11.5z" /><circle cx="8.5" cy="8.5" r="1.4" fill="currentColor" stroke="none" /></symbol>
        <symbol id="i-bag" viewBox="0 0 24 24"><path d="M6 8h12l1 12H5z" /><path d="M9 8V6a3 3 0 0 1 6 0v2" /></symbol>
        <symbol id="i-upload" viewBox="0 0 24 24"><path d="M12 16V5" /><polyline points="7 9 12 4 17 9" /><path d="M5 19h14" /></symbol>
        <symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6z" /><polyline points="9 12 11.5 14.5 16 9.5" /></symbol>
        <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" /><polyline points="12 7 12 12 16 14" /></symbol>
        <symbol id="i-filter" viewBox="0 0 24 24"><line x1="6" y1="7" x2="20" y2="7" /><line x1="9" y1="12" x2="20" y2="12" /><line x1="12" y1="17" x2="20" y2="17" /><circle cx="5" cy="12" r="1.6" fill="currentColor" stroke="none" /></symbol>
        <symbol id="i-chevron-right" viewBox="0 0 24 24"><polyline points="9 6 15 12 9 18" /></symbol>
        <symbol id="i-x" viewBox="0 0 24 24"><line x1="6" y1="6" x2="18" y2="18" /><line x1="18" y1="6" x2="6" y2="18" /></symbol>
        <symbol id="i-wallet" viewBox="0 0 24 24"><rect x="3.5" y="6" width="17" height="13" rx="2" /><path d="M3.5 10h17" /><circle cx="16.5" cy="14" r="1.3" fill="currentColor" stroke="none" /></symbol>
        <symbol id="i-mail" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2" /><polyline points="3.5 6.5 12 13 20.5 6.5" /></symbol>
        <symbol id="i-pin" viewBox="0 0 24 24"><path d="M12 21s7-5.5 7-11a7 7 0 0 0-14 0c0 5.5 7 11 7 11z" /><circle cx="12" cy="10" r="2.6" /></symbol>
        <symbol id="i-award" viewBox="0 0 24 24"><circle cx="12" cy="9" r="5.5" /><path d="M8.5 13.5 7 21l5-2.5L17 21l-1.5-7.5" /></symbol>
        <symbol id="i-pencil" viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16z" /><line x1="13.5" y1="6.5" x2="17.5" y2="10.5" /></symbol>
        <symbol id="i-external" viewBox="0 0 24 24"><path d="M14 4h6v6" /><line x1="20" y1="4" x2="11" y2="13" /><path d="M18 13.5V19a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 19V8a1.5 1.5 0 0 1 1.5-1.5H11" /></symbol>
        <symbol id="i-building" viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" rx="1.5" /><line x1="9" y1="7" x2="10" y2="7" /><line x1="14" y1="7" x2="15" y2="7" /><line x1="9" y1="11" x2="10" y2="11" /><line x1="14" y1="11" x2="15" y2="11" /><path d="M10 21v-4h4v4" /></symbol>
        <symbol id="i-cap" viewBox="0 0 24 24"><path d="M12 4 2 9l10 5 10-5z" /><path d="M6 11v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5" /><line x1="21" y1="9" x2="21" y2="15" /></symbol>
        <symbol id="i-sliders" viewBox="0 0 24 24"><line x1="4" y1="8" x2="20" y2="8" /><line x1="4" y1="16" x2="20" y2="16" /><circle cx="10" cy="8" r="2.4" fill="currentColor" stroke="none" /><circle cx="16" cy="16" r="2.4" fill="currentColor" stroke="none" /></symbol>
        <symbol id="i-users" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.2" /><path d="M3 19c0-3.2 2.7-5.5 6-5.5s6 2.3 6 5.5" /><path d="M16 5.2a3.2 3.2 0 0 1 0 5.9" /><path d="M17 13.6c2.3.5 4 2.4 4 5.1" /></symbol>
        <symbol id="i-book" viewBox="0 0 24 24"><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H20v18H7.5A2.5 2.5 0 0 0 5 22.5z" /><path d="M5 4.5v18" /><line x1="9" y1="7" x2="17" y2="7" /><line x1="9" y1="11" x2="16" y2="11" /></symbol>
      </defs>
    </svg>
  );
}
