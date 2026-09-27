// Batch 3 - job board (FR-13/14), Job Agent activity (FR-17/18),
// training partners + showcased students (FR-15), talent pool (FR-16).

export const TRACKS = ['RPA Developer', 'Business Analyst', 'Project Manager', 'Solution Architect'];
export const JOB_TYPES = ['Full-time', 'Contract', 'Project gig'];

export const jobPostings = [
  {
    id: 'rpa-dev-fintech',
    title: 'RPA Developer - Fintech Ops',
    company: 'Kudi Financial',
    companyAvatar: 'K',
    verifiedEmployer: true,
    track: 'RPA Developer',
    type: 'Full-time',
    location: 'Remote (Nigeria)',
    salary: '₦600,000 – ₦900,000 / month',
    salaryMin: 600000,
    posted: '2 days ago',
    applicants: 14,
    minTrust: 80,
    skills: ['Power Automate', 'Reconciliation', 'SQL'],
    about: 'Kudi Financial runs reconciliation and settlement automations across three banking partners.',
    description:
      'Own and extend our Power Automate reconciliation flows: bank statement ingestion, exception handling, and the month-end close pack. You will work directly with the finance team and a small platform squad.',
    responsibilities: [
      'Maintain and extend production reconciliation flows in Power Automate',
      'Design exception-handling and human-in-the-loop review steps',
      'Instrument flows with logging and alerting for auditability',
      'Pair with finance to translate close processes into automation',
    ],
  },
  {
    id: 'ba-automation',
    title: 'Business Analyst, Automation',
    company: 'Norebase',
    companyAvatar: 'N',
    verifiedEmployer: true,
    track: 'Business Analyst',
    type: 'Full-time',
    location: 'Lagos, NG · Hybrid',
    salary: '₦450,000 – ₦650,000 / month',
    salaryMin: 450000,
    posted: '4 days ago',
    applicants: 9,
    minTrust: 70,
    skills: ['Process mapping', 'Requirements', 'SQL', 'Stakeholder management'],
    about: 'Norebase helps companies expand across Africa; the ops team is automating compliance workflows.',
    description:
      'Shadow operations teams, map current-state processes, and write the requirements that our RPA developers build from. You are the bridge between messy reality and a clean automation spec.',
    responsibilities: [
      'Run process-discovery sessions and produce as-is / to-be maps',
      'Write automation requirement specs with clear acceptance criteria',
      'Prioritise a backlog of automation candidates by effort and payoff',
      'Validate delivered automations against the spec before sign-off',
    ],
  },
  {
    id: 'pm-rpa-rollout',
    title: 'Project Manager, RPA Rollout',
    company: 'Access Corp',
    companyAvatar: 'A',
    verifiedEmployer: true,
    track: 'Project Manager',
    type: 'Contract',
    location: 'Abuja, NG · On-site',
    salary: '₦800,000 / month (6-month contract)',
    salaryMin: 800000,
    posted: '1 week ago',
    applicants: 6,
    minTrust: 75,
    skills: ['Delivery management', 'RPA programmes', 'Governance', 'Vendor management'],
    about: 'Access Corp is standing up an internal RPA centre of excellence across 4 business units.',
    description:
      'Run the delivery of a 6-month RPA rollout: intake, prioritisation, build scheduling, UAT, and go-live governance across four business units.',
    responsibilities: [
      'Own the delivery plan, RAID log, and steering-committee reporting',
      'Coordinate developers, BAs, and business owners across units',
      'Enforce the sandbox verification and change-control gates',
      'Track benefits realisation against the business case',
    ],
  },
  {
    id: 'solution-architect-ai',
    title: 'Solution Architect, AI Platform',
    company: 'Terragon',
    companyAvatar: 'T',
    verifiedEmployer: true,
    track: 'Solution Architect',
    type: 'Full-time',
    location: 'Remote (Global)',
    salary: 'Competitive · USD',
    salaryMin: 0,
    posted: '1 week ago',
    applicants: 21,
    minTrust: 85,
    skills: ['Solution design', 'LLM orchestration', 'Security architecture', 'Cloud'],
    about: 'Terragon builds data and AI products for consumer brands across Africa.',
    description:
      'Design the reference architecture for our AI automation platform: sandboxed execution, model gateways, escrow-grade audit logging, and multi-tenant isolation.',
    responsibilities: [
      'Own the target architecture and the tech-radar for automation execution',
      'Design the isolated, network-restricted sandbox for untrusted code',
      'Set security and data-protection patterns (NDPA-aligned)',
      'Review high-risk designs from delivery squads',
    ],
  },
  {
    id: 'rpa-gig-invoices',
    title: 'Build an invoice-capture bot (project gig)',
    company: 'Bloom Retail',
    companyAvatar: 'B',
    verifiedEmployer: true,
    track: 'RPA Developer',
    type: 'Project gig',
    location: 'Remote',
    salary: '₦350,000 fixed',
    salaryMin: 350000,
    posted: '3 days ago',
    applicants: 11,
    minTrust: 70,
    skills: ['Python', 'OCR', 'Email automation'],
    about: 'Bloom Retail is a 40-store chain automating supplier invoice capture.',
    description:
      'One-off build: watch a shared mailbox, extract supplier invoice fields with OCR, validate against POs, and push to the accounting system. Handover with docs and a short walkthrough.',
    responsibilities: [
      'Mailbox watcher + attachment handling',
      'OCR extraction with a confidence threshold for manual review',
      'PO matching and exception report',
      'Documentation and a recorded handover',
    ],
  },
  {
    id: 'ba-contract-telco',
    title: 'Business Analyst - RPA (contract)',
    company: 'MTN Digital',
    companyAvatar: 'M',
    verifiedEmployer: true,
    track: 'Business Analyst',
    type: 'Contract',
    location: 'Lagos, NG · Hybrid',
    salary: '₦700,000 / month (12-month contract)',
    salaryMin: 700000,
    posted: '5 days ago',
    applicants: 8,
    minTrust: 78,
    skills: ['Process mining', 'Requirements', 'Telco billing', 'Six Sigma'],
    about: 'MTN Digital is automating assurance and billing-exception workflows.',
    description:
      'Analyse billing-exception and revenue-assurance processes, quantify leakage, and spec the automations that close the gaps.',
    responsibilities: [
      'Process-mine current billing-exception handling',
      'Quantify revenue leakage and prioritise fixes',
      'Spec automations and define control points',
      'Support UAT and post-go-live tuning',
    ],
  },
];

export const getJob = (id) => jobPostings.find((j) => j.id === id) || null;

// ---- Candidate side: my applications ----
export const APP_STATUS = {
  applied: { label: 'Applied', tone: 'info' },
  in_review: { label: 'In review', tone: 'warn' },
  interview: { label: 'Interview', tone: 'ok' },
  offer: { label: 'Offer', tone: 'ok' },
  rejected: { label: 'Not selected', tone: 'bad' },
};

export const myApplications = [
  { id: 'a1', jobId: 'rpa-dev-fintech', title: 'RPA Developer - Fintech Ops', company: 'Kudi Financial', appliedAt: 'Sep 3, 2026', via: 'agent', fit: 94, status: 'in_review' },
  { id: 'a2', jobId: 'pm-rpa-rollout', title: 'Project Manager, RPA Rollout', company: 'Access Corp', appliedAt: 'Sep 1, 2026', via: 'agent', fit: 88, status: 'interview' },
  { id: 'a3', jobId: 'ba-contract-telco', title: 'Business Analyst - RPA (contract)', company: 'MTN Digital', appliedAt: 'Aug 28, 2026', via: 'manual', fit: 82, status: 'applied' },
  { id: 'a4', jobId: 'rpa-gig-invoices', title: 'Build an invoice-capture bot', company: 'Bloom Retail', appliedAt: 'Aug 20, 2026', via: 'manual', fit: 79, status: 'rejected' },
];

// ---- Job Agent ----
export const agentDefaults = { enabled: true, threshold: 85 };

export const agentActivity = [
  { id: 'g1', jobId: 'rpa-dev-fintech', title: 'RPA Developer - Fintech Ops', company: 'Kudi Financial', track: 'RPA Developer', fit: 94, at: '2h ago', reason: 'Strong match on Power Automate + reconciliation; trust score above the employer minimum.' },
  { id: 'g2', jobId: 'pm-rpa-rollout', title: 'Project Manager, RPA Rollout', company: 'Access Corp', track: 'Project Manager', fit: 88, at: '1d ago', reason: 'Delivery-management history and RPA programme exposure matched.' },
  { id: 'g3', jobId: 'ba-automation', title: 'Business Analyst, Automation', company: 'Norebase', track: 'Business Analyst', fit: 81, at: '1d ago', reason: 'Requirements and process-mapping match, but no recent BA-titled marketplace work.' },
  { id: 'g4', jobId: 'ba-contract-telco', title: 'Business Analyst - RPA (contract)', company: 'MTN Digital', track: 'Business Analyst', fit: 79, at: '2d ago', reason: 'Telco-billing domain gap; core BA skills present.' },
  { id: 'g5', jobId: 'solution-architect-ai', title: 'Solution Architect, AI Platform', company: 'Terragon', track: 'Solution Architect', fit: 63, at: '2d ago', reason: 'No solution-architecture or security-architecture history on your verified profile.' },
  { id: 'g6', jobId: 'rpa-gig-invoices', title: 'Build an invoice-capture bot', company: 'Bloom Retail', track: 'RPA Developer', fit: 86, at: '3d ago', reason: 'Python + OCR + email-automation match; fixed-price gig within your history.' },
];

// ---- Training partners (FR-15) ----
export const trainingPartners = [
  {
    id: 'semicolon',
    name: 'Semicolon Africa',
    avatar: 'SA',
    accredited: true,
    type: 'Software & RPA academy',
    location: 'Lagos, Nigeria',
    cohorts: 13,
    blurb:
      'A two-year software and RPA programme. Graduates ship real marketplace projects during training, so their trust score reflects delivered work - not just a certificate.',
    students: [
      { handle: 'chidera-eze', name: 'Chidera Eze', avatar: 'C', track: 'RPA Developer', trustScore: 88, projects: 6, rating: 4.8, hired: false },
      { handle: 'musa-bello', name: 'Musa Bello', avatar: 'M', track: 'RPA Developer', trustScore: 84, projects: 4, rating: 4.7, hired: true },
      { handle: 'aisha-lawal', name: 'Aisha Lawal', avatar: 'A', track: 'Business Analyst', trustScore: 82, projects: 5, rating: 4.6, hired: false },
      { handle: 'tobi-manuel', name: 'Tobi Manuel', avatar: 'T', track: 'Solution Architect', trustScore: 90, projects: 7, rating: 4.9, hired: false },
      { handle: 'ada-okonkwo', name: 'Ada Okonkwo', avatar: 'A', track: 'Project Manager', trustScore: 86, projects: 5, rating: 4.7, hired: true },
    ],
  },
  {
    id: 'altschool',
    name: 'AltSchool Africa',
    avatar: 'AS',
    accredited: true,
    type: 'Online engineering school',
    location: 'Remote · pan-African',
    cohorts: 8,
    blurb:
      'Part-time engineering tracks with an automation specialisation. Showcased learners have each completed at least three verified marketplace deliveries.',
    students: [
      { handle: 'kelvin-osei', name: 'Kelvin Osei', avatar: 'K', track: 'RPA Developer', trustScore: 80, projects: 3, rating: 4.5, hired: false },
      { handle: 'ngozi-udo', name: 'Ngozi Udo', avatar: 'N', track: 'Business Analyst', trustScore: 83, projects: 4, rating: 4.6, hired: false },
      { handle: 'femi-adeyemi', name: 'Femi Adeyemi', avatar: 'F', track: 'RPA Developer', trustScore: 87, projects: 5, rating: 4.8, hired: true },
    ],
  },
  {
    id: 'access-academy',
    name: 'Access RPA Academy',
    avatar: 'AA',
    accredited: true,
    type: 'Corporate training arm',
    location: 'Lagos, Nigeria',
    cohorts: 4,
    blurb:
      'The in-house RPA academy of a tier-1 bank, opening its top graduates to the wider market. Training is banking-grade with a security-first curriculum.',
    students: [
      { handle: 'blessing-nwosu', name: 'Blessing Nwosu', avatar: 'B', track: 'RPA Developer', trustScore: 85, projects: 4, rating: 4.7, hired: false },
      { handle: 'ibrahim-sani', name: 'Ibrahim Sani', avatar: 'I', track: 'Project Manager', trustScore: 82, projects: 3, rating: 4.5, hired: false },
    ],
  },
];

export const getPartner = (id) => trainingPartners.find((p) => p.id === id) || null;

// ---- Talent pool (FR-16): marketplace sellers + showcased students ----
const marketplaceTalent = [
  { handle: 'abdul-r', name: 'Abdul R.', avatar: 'A', track: 'RPA Developer', trustScore: 96, projects: 42, rating: 4.9, source: 'Marketplace', skills: ['Power Automate', 'Finance', 'Reconciliation'], openToWork: false, location: 'Abuja, Nigeria' },
  { handle: 'ibrahim-d', name: 'Ibrahim D.', avatar: 'I', track: 'RPA Developer', trustScore: 91, projects: 28, rating: 4.8, source: 'Marketplace', skills: ['Python', 'Scraping', 'ETL'], openToWork: true, location: 'Kano, Nigeria' },
  { handle: 'grace-n', name: 'Grace N.', avatar: 'G', track: 'Business Analyst', trustScore: 84, projects: 17, rating: 4.5, source: 'Marketplace', skills: ['Python', 'HR tech', 'ATS APIs'], openToWork: true, location: 'Enugu, Nigeria' },
  { handle: 'chuka-o', name: 'Chuka O.', avatar: 'C', track: 'Solution Architect', trustScore: 89, projects: 11, rating: 4.6, source: 'Marketplace', skills: ['DevOps', 'Incident response', 'Python'], openToWork: false, location: 'Port Harcourt, Nigeria' },
];

export const talentPool = [
  ...marketplaceTalent,
  ...trainingPartners.flatMap((p) =>
    p.students.map((s) => ({
      handle: s.handle,
      name: s.name,
      avatar: s.avatar,
      track: s.track,
      trustScore: s.trustScore,
      projects: s.projects,
      rating: s.rating,
      source: p.name,
      partnerId: p.id,
      skills: [s.track, 'Automation'],
      openToWork: !s.hired,
      location: p.location,
    })),
  ),
];

export const ALL_SKILLS = [
  'Power Automate', 'Python', 'Reconciliation', 'Process mapping', 'Requirements',
  'SQL', 'DevOps', 'Solution design', 'OCR', 'ETL', 'Automation',
];
