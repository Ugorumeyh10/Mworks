from datetime import datetime, timedelta, timezone

JOBS = [
    {
        "slug": "rpa-dev-fintech",
        "title": "RPA Developer - Fintech Ops",
        "company": "Kudi Financial",
        "company_avatar": "K",
        "poster_email": "kudi@mworks.ng",
        "poster_name": "Kudi Financial",
        "track": "RPA Developer",
        "type": "Full-time",
        "location": "Remote (Nigeria)",
        "salary": "₦600,000 – ₦900,000 / month",
        "salary_min": 600000,
        "min_trust": 80,
        "skills": ["Power Automate", "Reconciliation", "SQL"],
        "about": "Kudi Financial runs reconciliation and settlement automations across three banking partners.",
        "description": (
            "Own and extend our Power Automate reconciliation flows: bank statement ingestion, "
            "exception handling, and the month-end close pack. You will work directly with the finance team and a small platform squad."
        ),
        "responsibilities": [
            "Maintain and extend production reconciliation flows in Power Automate",
            "Design exception-handling and human-in-the-loop review steps",
            "Instrument flows with logging and alerting for auditability",
            "Pair with finance to translate close processes into automation",
        ],
        "applicants": 14,
        "age_days": 2,
    },
    {
        "slug": "ba-automation",
        "title": "Business Analyst, Automation",
        "company": "Norebase",
        "company_avatar": "N",
        "poster_email": "jobs@norebase.mworks.ng",
        "poster_name": "Norebase Talent",
        "track": "Business Analyst",
        "type": "Full-time",
        "location": "Lagos, NG · Hybrid",
        "salary": "₦450,000 – ₦650,000 / month",
        "salary_min": 450000,
        "min_trust": 70,
        "skills": ["Process mapping", "Requirements", "SQL", "Stakeholder management"],
        "about": "Norebase helps companies expand across Africa; the ops team is automating compliance workflows.",
        "description": (
            "Shadow operations teams, map current-state processes, and write the requirements that our RPA developers build from. "
            "You are the bridge between messy reality and a clean automation spec."
        ),
        "responsibilities": [
            "Run process-discovery sessions and produce as-is / to-be maps",
            "Write automation requirement specs with clear acceptance criteria",
            "Prioritise a backlog of automation candidates by effort and payoff",
            "Validate delivered automations against the spec before sign-off",
        ],
        "applicants": 9,
        "age_days": 4,
    },
    {
        "slug": "pm-rpa-rollout",
        "title": "Project Manager, RPA Rollout",
        "company": "Access Corp",
        "company_avatar": "A",
        "poster_email": "rpa@access.mworks.ng",
        "poster_name": "Access Corp RPA",
        "track": "Project Manager",
        "type": "Contract",
        "location": "Abuja, NG · On-site",
        "salary": "₦800,000 / month (6-month contract)",
        "salary_min": 800000,
        "min_trust": 75,
        "skills": ["Delivery management", "RPA programmes", "Governance", "Vendor management"],
        "about": "Access Corp is standing up an internal RPA centre of excellence across 4 business units.",
        "description": (
            "Run the delivery of a 6-month RPA rollout: intake, prioritisation, build scheduling, UAT, "
            "and go-live governance across four business units."
        ),
        "responsibilities": [
            "Own the delivery plan, RAID log, and steering-committee reporting",
            "Coordinate developers, BAs, and business owners across units",
            "Enforce the sandbox verification and change-control gates",
            "Track benefits realisation against the business case",
        ],
        "applicants": 6,
        "age_days": 7,
    },
    {
        "slug": "solution-architect-ai",
        "title": "Solution Architect, AI Platform",
        "company": "Terragon",
        "company_avatar": "T",
        "poster_email": "arch@terragon.mworks.ng",
        "poster_name": "Terragon Platform",
        "track": "Solution Architect",
        "type": "Full-time",
        "location": "Remote (Global)",
        "salary": "Competitive · USD",
        "salary_min": 0,
        "min_trust": 85,
        "skills": ["Solution design", "LLM orchestration", "Security architecture", "Cloud"],
        "about": "Terragon builds data and AI products for consumer brands across Africa.",
        "description": (
            "Design the reference architecture for our AI automation platform: sandboxed execution, "
            "model gateways, escrow-grade audit logging, and multi-tenant isolation."
        ),
        "responsibilities": [
            "Own the target architecture and the tech-radar for automation execution",
            "Design the isolated, network-restricted sandbox for untrusted code",
            "Set security and data-protection patterns (NDPA-aligned)",
            "Review high-risk designs from delivery squads",
        ],
        "applicants": 21,
        "age_days": 7,
    },
    {
        "slug": "rpa-gig-invoices",
        "title": "Build an invoice-capture bot (project gig)",
        "company": "Bloom Retail",
        "company_avatar": "B",
        "poster_email": "ops@bloom.mworks.ng",
        "poster_name": "Bloom Retail Ops",
        "track": "RPA Developer",
        "type": "Project gig",
        "location": "Remote",
        "salary": "₦350,000 fixed",
        "salary_min": 350000,
        "min_trust": 70,
        "skills": ["Python", "OCR", "Email automation"],
        "about": "Bloom Retail is a 40-store chain automating supplier invoice capture.",
        "description": (
            "One-off build: watch a shared mailbox, extract supplier invoice fields with OCR, validate against POs, "
            "and push to the accounting system. Handover with docs and a short walkthrough."
        ),
        "responsibilities": [
            "Mailbox watcher + attachment handling",
            "OCR extraction with a confidence threshold for manual review",
            "PO matching and exception report",
            "Documentation and a recorded handover",
        ],
        "applicants": 11,
        "age_days": 3,
    },
    {
        "slug": "ba-contract-telco",
        "title": "Business Analyst - RPA (contract)",
        "company": "MTN Digital",
        "company_avatar": "M",
        "poster_email": "digital@mtn.mworks.ng",
        "poster_name": "MTN Digital Hiring",
        "track": "Business Analyst",
        "type": "Contract",
        "location": "Lagos, NG · Hybrid",
        "salary": "₦700,000 / month (12-month contract)",
        "salary_min": 700000,
        "min_trust": 78,
        "skills": ["Process mining", "Requirements", "Telco billing", "Six Sigma"],
        "about": "MTN Digital is automating assurance and billing-exception workflows.",
        "description": "Analyse billing-exception and revenue-assurance processes, quantify leakage, and spec the automations that close the gaps.",
        "responsibilities": [
            "Process-mine current billing-exception handling",
            "Quantify revenue leakage and prioritise fixes",
            "Spec automations and define control points",
            "Support UAT and post-go-live tuning",
        ],
        "applicants": 8,
        "age_days": 5,
    },
]


HENRY_APPLICATIONS = [
    {"slug": "rpa-dev-fintech", "via": "agent", "fit": 94, "status": "in_review", "age_days": 10},
    {"slug": "pm-rpa-rollout", "via": "agent", "fit": 88, "status": "interview", "age_days": 12},
    {"slug": "ba-contract-telco", "via": "manual", "fit": 82, "status": "applied", "age_days": 16},
    {"slug": "rpa-gig-invoices", "via": "manual", "fit": 79, "status": "rejected", "age_days": 24},
]


def job_created_at(age_days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=age_days)
