import { useId } from 'react';
import './BrandMark.css';

/**
 * Mworks mark: rotated Ankara checker (gold, terracotta, forest, indigo)
 * with a safari gold rim and cream M.
 */
export default function BrandMark({ size = 32, withWord = false, word = 'Mworks' }) {
  const uid = useId().replace(/:/g, '');
  const pid = `ankara-${uid}`;
  const gid = `goldrim-${uid}`;

  return (
    <span className={`brand-lockup${withWord ? ' with-word' : ''}`}>
      <svg
        className="brand-mark-svg"
        width={size}
        height={size}
        viewBox="0 0 40 40"
        aria-hidden="true"
      >
        <defs>
          <pattern
            id={pid}
            width="10"
            height="10"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45 5 5)"
          >
            <rect width="10" height="10" fill="#C9A227" />
            <rect width="5" height="5" fill="#C45C26" />
            <rect x="5" y="5" width="5" height="5" fill="#1F4D3A" />
            <rect x="5" y="0" width="5" height="5" fill="#2C2A6B" />
          </pattern>
          <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#F6E7B2" />
            <stop offset="50%" stopColor="#C9A227" />
            <stop offset="100%" stopColor="#8B6914" />
          </linearGradient>
        </defs>
        <rect width="40" height="40" rx="10" fill={`url(#${pid})`} />
        <rect
          x="1.4"
          y="1.4"
          width="37.2"
          height="37.2"
          rx="8.6"
          fill="none"
          stroke={`url(#${gid})`}
          strokeWidth="1.8"
        />
        <text
          x="20"
          y="27.5"
          textAnchor="middle"
          fontFamily="Bricolage Grotesque, sans-serif"
          fontWeight="800"
          fontSize="19"
          fill="#FFF8E7"
        >
          M
        </text>
      </svg>
      {withWord && <span className="brand-word">{word}</span>}
    </span>
  );
}
