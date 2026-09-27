export const posts = [
  {
    id: 'invoice-bot',
    type: 'automation',
    title: 'Invoice Reconciliation Bot',
    seller: { name: 'Abdul R.', avatar: 'A', trust: 96 },
    caption: 'Reconciles bank statements against invoices automatically - built for mid-size finance teams.',
    metric: '92% fewer errors · 340 invoices/hr',
    price: '₦650,000',
    likes: 214,
    comments: 38,
    tags: ['Power Automate', 'Finance'],
    metrics: [
      { label: 'Error reduction', value: '92%' },
      { label: 'Invoices processed', value: '340/hr' },
      { label: 'Seller trust score', value: '96' },
    ],
    description:
      'Reconciles bank statement lines against outstanding invoices, flags mismatches, and exports a discrepancy report. Sandbox-verified on real transaction data.',
    verificationLog: [
      { label: 'Sandbox execution', status: 'Passed' },
      { label: 'Declared metrics check', status: 'Matched' },
      { label: 'Security scan', status: 'Clean' },
    ],
    reviews: [
      { author: 'Chidinma O.', text: 'Cut our month-end close by two days.' },
      { author: 'Femi A.', text: 'Setup took an afternoon, worked immediately.' },
    ],
    sellerSub: '42 sales, 4.9★ from 118 reviews, verified since 2025',
  },
  {
    id: 'cohort-12',
    type: 'training',
    partnerId: 'semicolon',
    title: 'Cohort 12 Showcase - Semicolon Africa',
    seller: { name: 'Semicolon Africa', avatar: 'SA', org: true, partner: true },
    caption:
      'Our top 5 RPA graduates this cohort - each carries a verified trust score from real marketplace projects, not just a certificate.',
    likes: 512,
    comments: 61,
    verifiedLabel: 'Verified cohort',
  },
  {
    id: 'job-rpa-dev',
    type: 'job',
    title: 'RPA Developer, fintech ops',
    meta: 'Remote (Nigeria) - ₦600k–900k/month',
    caption:
      'Building reconciliation flows in Power Automate. A verified Mworks trust score is preferred over a resume alone.',
    likes: 89,
    comments: 12,
  },
  {
    id: 'support-prompts',
    type: 'prompt',
    title: 'Customer support prompt pack',
    seller: { name: 'Tolu O.', avatar: 'T', trust: 88 },
    caption: '12-prompt pack for AI customer support triage. Works with GPT and Claude.',
    price: '₦25,000',
    likes: 143,
    comments: 22,
    verifiedLabel: 'Originality checked',
  },
];

export const jobs = [
  {
    id: 1,
    title: 'RPA Developer - Fintech Ops',
    meta: 'Remote (Nigeria) · ₦600k–900k/month',
    fit: 94,
    status: 'applied',
    statusLabel: 'Applied automatically · 2h ago',
  },
  {
    id: 2,
    title: 'Business Analyst, Automation',
    meta: 'Lagos, NG · Hybrid',
    fit: 81,
    status: 'review',
    statusLabel: 'Needs your review',
  },
  {
    id: 3,
    title: 'Solution Architect, AI Platform',
    meta: 'Remote (Global)',
    fit: 65,
    status: 'skipped',
    statusLabel: 'Not a strong fit - skipped',
  },
  {
    id: 4,
    title: 'Project Manager, RPA Rollout',
    meta: 'Abuja, NG · On-site',
    fit: 88,
    status: 'applied',
    statusLabel: 'Applied automatically · 1d ago',
  },
];

export const roleFilters = [
  'All roles',
  'RPA Developer',
  'Business Analyst',
  'Project Manager',
  'Solution Architect',
];

export const conversations = [
  {
    id: 1,
    name: 'Abdul R.',
    avatar: 'A',
    preview: 'Sent you the updated demo video',
    time: '2m',
    unread: true,
  },
  {
    id: 2,
    name: 'Semicolon Africa',
    avatar: 'SA',
    org: true,
    preview: 'Cohort 13 applications open next week',
    time: '1h',
  },
  {
    id: 3,
    name: 'Fintech Ops (Employer)',
    avatar: 'FO',
    steel: true,
    preview: 'Can you hop on a call Thursday?',
    time: '3h',
    unread: true,
  },
  {
    id: 4,
    name: 'Tolu O.',
    avatar: 'T',
    preview: 'Thanks for the review!',
    time: '1d',
  },
];

export const initialAssistantMessages = [
  { from: 'bot', text: "Hi Henry - your Invoice Reconciliation Bot passed sandbox testing this morning and is live now." },
  { from: 'me', text: 'Nice. What about the new prompt pack?' },
  { from: 'bot', text: "Still in the originality check queue - usually done within 10 minutes. I'll notify you." },
  { from: 'me', text: 'Also, did the RPA Developer application go through?' },
  { from: 'bot', text: 'Yes - applied automatically 2 hours ago at a 94% profile fit. Your verified trust score went with it.' },
];
