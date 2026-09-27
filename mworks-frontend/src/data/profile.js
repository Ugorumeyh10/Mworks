// Profiles (Batch 2). Powers /u/:handle and /settings/profile.
import { listings } from './marketplace.js';
import { talentPool } from './jobs.js';

export const slug = (name) =>
  name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

export const currentUser = {
  handle: 'henry',
  name: 'Henry Okafor',
  avatar: 'H',
  isMe: true,
  roles: ['buyer', 'seller'],
  headline: 'RPA & AI automation builder - ex-banking RPA CoE',
  location: 'Lagos, Nigeria',
  memberSince: 'Jan 2026',
  trustScore: 93,
  points: 1840,
  rating: 4.8,
  ratingCount: 19,
  identity: {
    status: 'verified',
    verifiedOn: 'Feb 2026',
    checks: [
      { label: 'Email address', status: 'done' },
      { label: 'Government ID (NIN / passport)', status: 'done' },
      { label: 'Proof of address', status: 'done' },
    ],
  },
  skills: ['Power Automate', 'Python', 'Reconciliation', 'Prompt engineering', 'Data pipelines'],
  links: [
    { label: 'GitHub', url: 'github.com/henryokafor' },
    { label: 'LinkedIn', url: 'linkedin.com/in/henryokafor' },
  ],
  stats: { sales: 27, completionRate: 100, avgResponse: '2h', disputes: 0 },
  pointsBreakdown: [
    { label: 'Completed transactions', value: 1350 },
    { label: 'Positive reviews', value: 420 },
    { label: 'Verified identity bonus', value: 70 },
  ],
};

const others = [
  {
    name: 'Abdul R.', avatar: 'A', roles: ['seller'],
    headline: 'Power Automate specialist - finance & reconciliation automations',
    location: 'Abuja, Nigeria', memberSince: '2025',
    trustScore: 96, points: 4120, rating: 4.9, ratingCount: 118,
    identity: { status: 'verified', verifiedOn: '2025' },
    skills: ['Power Automate', 'Finance', 'Reconciliation', 'Escrow flows'],
    stats: { sales: 42, completionRate: 98, avgResponse: '1h', disputes: 1 },
  },
  {
    name: 'Tolu O.', avatar: 'T', roles: ['seller', 'buyer'],
    headline: 'Prompt engineer - customer support & ops prompt packs',
    location: 'Ibadan, Nigeria', memberSince: '2025',
    trustScore: 88, points: 2260, rating: 4.7, ratingCount: 54,
    identity: { status: 'verified', verifiedOn: '2025' },
    skills: ['Prompt engineering', 'Support ops', 'LLM evaluation'],
    stats: { sales: 63, completionRate: 95, avgResponse: '4h', disputes: 0 },
  },
  {
    name: 'Ibrahim D.', avatar: 'I', roles: ['seller'],
    headline: 'Python automation & data engineering',
    location: 'Kano, Nigeria', memberSince: '2024',
    trustScore: 91, points: 3010, rating: 4.8, ratingCount: 31,
    identity: { status: 'verified', verifiedOn: '2024' },
    skills: ['Python', 'Scraping', 'ETL', 'Airflow'],
    stats: { sales: 28, completionRate: 97, avgResponse: '3h', disputes: 0 },
  },
  {
    name: 'Grace N.', avatar: 'G', roles: ['seller'],
    headline: 'HR tech automations - screening & ATS integrations',
    location: 'Enugu, Nigeria', memberSince: '2025',
    trustScore: 84, points: 990, rating: 4.5, ratingCount: 12,
    identity: { status: 'pending' },
    skills: ['Python', 'HR tech', 'ATS APIs'],
    stats: { sales: 17, completionRate: 92, avgResponse: '6h', disputes: 1 },
  },
  {
    name: 'Amara U.', avatar: 'A', roles: ['seller'],
    headline: 'Marketing & SEO prompt chains',
    location: 'Lagos, Nigeria', memberSince: '2024',
    trustScore: 90, points: 3480, rating: 4.8, ratingCount: 76,
    identity: { status: 'verified', verifiedOn: '2024' },
    skills: ['SEO', 'Content ops', 'Prompt engineering'],
    stats: { sales: 88, completionRate: 96, avgResponse: '2h', disputes: 0 },
  },
  {
    name: 'Chuka O.', avatar: 'C', roles: ['seller'],
    headline: 'DevOps & incident automation',
    location: 'Port Harcourt, Nigeria', memberSince: '2025',
    trustScore: 89, points: 1670, rating: 4.6, ratingCount: 8,
    identity: { status: 'verified', verifiedOn: '2025' },
    skills: ['Python', 'DevOps', 'Incident response', 'Slack apps'],
    stats: { sales: 11, completionRate: 94, avgResponse: '5h', disputes: 0 },
  },
];

const baseProfiles = [
  currentUser,
  ...others.map((p) => ({ handle: slug(p.name), links: [], pointsBreakdown: [], ...p })),
];

// Lightweight profiles for showcased students / candidates so /u/:handle
// resolves for everyone in the talent pool (FR-15 links each to a real profile).
const talentProfiles = talentPool
  .filter((t) => !baseProfiles.some((p) => p.handle === t.handle))
  .map((t) => ({
    handle: t.handle,
    name: t.name,
    avatar: t.avatar,
    roles: ['candidate'],
    headline: `${t.track} · ${t.source === 'Marketplace' ? 'marketplace practitioner' : t.source + ' graduate'}`,
    location: t.location,
    memberSince: '2026',
    trustScore: t.trustScore,
    points: t.trustScore * 20,
    rating: t.rating,
    ratingCount: t.projects,
    identity: { status: 'verified', verifiedOn: '2026' },
    skills: t.skills,
    links: [],
    stats: { sales: t.projects, completionRate: 95, avgResponse: '1 day', disputes: 0 },
    pointsBreakdown: [],
    openToWork: t.openToWork,
    trainingPartner: t.source === 'Marketplace' ? null : t.source,
  }));

export const profiles = [...baseProfiles, ...talentProfiles];

export const getProfile = (handle) => profiles.find((p) => p.handle === handle) || null;

export const listingsBySeller = (name) => listings.filter((l) => l.seller.name === name);
export const reviewsForSeller = (name) =>
  listings
    .filter((l) => l.seller.name === name)
    .flatMap((l) => (l.reviews || []).map((r) => ({ ...r, listing: l.title })));
