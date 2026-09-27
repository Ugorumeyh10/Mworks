from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session

from app.catalog_jobs import HENRY_APPLICATIONS, JOBS, job_created_at
from app.config import Settings
from app.models import AgentPref, BlogPost, ChatMessage, Conversation, Job, JobApplication, Listing, User
from app.security import hash_password
from app.storage import put_bytes

log = logging.getLogger("mworks")


def _seller(db: Session, email: str, name: str, trust: int, sales: int, rating: float, reviews: int, password: str) -> User:
    row = db.query(User).filter(User.email == email).one_or_none()
    if row:
        return row
    row = User(
        email=email,
        name=name,
        role="both",
        password_hash=hash_password(password),
        trust_score=trust,
        sales_count=sales,
        rating=rating,
        review_count=reviews,
        country="Nigeria",
    )
    db.add(row)
    db.flush()
    return row


CATALOG = [
    {
        "slug": "invoice-bot",
        "type": "automation",
        "title": "Invoice Reconciliation Bot",
        "blurb": "Reconciles bank statements against invoices automatically, built for mid-size finance teams.",
        "description": "Reconciles bank statement lines against outstanding invoices, flags mismatches, and exports a discrepancy report. Sandbox-verified on real transaction data.",
        "category": "Finance",
        "platform": "Power Automate",
        "price": 650000,
        "verified": True,
        "verify": "sandbox",
        "tags": ["Power Automate", "Finance", "Reconciliation"],
        "metrics": [
            {"label": "Error reduction", "value": "92%"},
            {"label": "Invoices processed", "value": "340/hr"},
            {"label": "Seller trust score", "value": "96"},
        ],
        "seller_email": "abdul@mworks.ng",
        "seller_name": "Abdul R.",
        "trust": 96,
        "sales": 42,
        "rating": 4.9,
        "reviews_n": 118,
        "reviews": [{"author": "Chidinma O.", "stars": 5, "text": "Cut our month-end close by two days."}],
    },
    {
        "slug": "support-prompts",
        "type": "prompt",
        "title": "Customer Support Prompt Pack",
        "blurb": "12-prompt pack for AI customer-support triage. Works with GPT and Claude.",
        "description": "Twelve chained prompts covering intake, sentiment tagging, priority routing, drafted replies, and escalation summaries.",
        "category": "Customer Support",
        "models": ["GPT-4o", "Claude", "Gemini"],
        "prompt_count": 12,
        "price": 25000,
        "verified": True,
        "verify": "originality",
        "tags": ["Support", "Prompt pack", "Triage"],
        "prompt_text": (
            "You are a customer-support triage assistant for a Nigerian fintech.\n"
            "Read the incoming ticket. Return JSON with keys: intent, sentiment, priority (P1-P4), "
            "language, and a draft reply in the customer's language.\n"
            "Never invent account balances or promise a refund. Escalate fraud, account lockout, "
            "and regulatory complaints as P1."
        ),
        "seller_email": "tolu@mworks.ng",
        "seller_name": "Tolu O.",
        "trust": 88,
        "sales": 63,
        "rating": 4.7,
        "reviews_n": 54,
        "reviews": [{"author": "Ngozi E.", "stars": 5, "text": "Dropped straight into our helpdesk workflow."}],
    },
    {
        "slug": "web-scraper",
        "type": "automation",
        "title": "Resilient Web Scraper Framework",
        "blurb": "Config-driven Python scraper with proxy rotation, retries, and CSV/JSON export.",
        "description": "A configurable scraping framework: declare targets in YAML, get structured output with automatic retry, rate-limiting, and proxy rotation.",
        "category": "Data & Scraping",
        "platform": "Python",
        "price": 240000,
        "verified": True,
        "verify": "sandbox",
        "tags": ["Python", "Scraping", "ETL"],
        "metrics": [{"label": "Uptime on test run", "value": "99.4%"}, {"label": "Pages/min", "value": "1,200"}],
        "seller_email": "ibrahim@mworks.ng",
        "seller_name": "Ibrahim D.",
        "trust": 91,
        "sales": 28,
        "rating": 4.8,
        "reviews_n": 31,
        "reviews": [],
    },
    {
        "slug": "hr-screener",
        "type": "automation",
        "title": "CV Screening & Shortlist Bot",
        "blurb": "Parses CVs, scores against a role rubric, and posts a ranked shortlist to your ATS.",
        "description": "Ingests a folder of CVs, extracts structured fields, scores each against a configurable rubric, and writes a ranked shortlist.",
        "category": "HR & Recruiting",
        "platform": "Python",
        "price": 180000,
        "verified": True,
        "verify": "sandbox",
        "tags": ["HR", "Screening", "ATS"],
        "metrics": [{"label": "Screening time saved", "value": "85%"}],
        "seller_email": "grace@mworks.ng",
        "seller_name": "Grace N.",
        "trust": 84,
        "sales": 17,
        "rating": 4.5,
        "reviews_n": 12,
        "reviews": [],
    },
    {
        "slug": "rpa-opportunity-canvas",
        "type": "document",
        "title": "RPA Opportunity Canvas",
        "blurb": "One-page BA template for scoring automation candidates by effort and payoff.",
        "description": "A fill-in canvas covering as-is pain, volume, exception rate, systems touched, and a recommended build/buy/skip call. Sold as a reusable template. Use Revise if you need it adapted to your process for a capped fee.",
        "category": "Process mapping",
        "price": 8500,
        "verified": True,
        "verify": "originality",
        "tags": ["BA", "RPA", "Template"],
        "license": "template",
        "seller_email": "ada@mworks.ng",
        "seller_name": "Ada Obi",
        "trust": 81,
        "sales": 34,
        "rating": 4.8,
        "reviews_n": 19,
        "reviews": [{"author": "Femi A.", "stars": 5, "text": "Used it in two discovery workshops the same week."}],
    },
    {
        "slug": "c4-architecture-pack",
        "type": "document",
        "title": "C4 Architecture Pack for RPA CoE",
        "blurb": "Context, container, and sequence diagrams plus an integration contract for a finance automation.",
        "description": "A solution-architect pack: C4 context and container views, a sequence for statement ingest, and a one-page integration contract. Preview is the table of contents and first two pages. Exclusive or template license at checkout.",
        "category": "Architecture",
        "price": 28000,
        "verified": True,
        "verify": "originality",
        "tags": ["C4", "Architecture", "Integration"],
        "license": "template",
        "seller_email": "kemi@mworks.ng",
        "seller_name": "Kemi Adeyemi",
        "trust": 90,
        "sales": 11,
        "rating": 4.9,
        "reviews_n": 7,
        "reviews": [],
    },
    {
        "slug": "ai-interviewer",
        "type": "agent",
        "title": "Mworks AI Interviewer",
        "blurb": "Hosted AI interviewer companies can trial, buy, hire, or download. Asks developers questions against profile, CV excerpts, and your RAG docs.",
        "description": (
            "A disclosed AI interviewer for RPA and AI developer hiring. Companies buy a hosted license, "
            "hire us to customize the rubric, or download the playbook. Upload role docs for retrieval. "
            "The agent asks one question at a time, never pretends to be human, and never executes candidate code. "
            "A human reviewer sees the transcript and scorecard. Free trial is capped."
        ),
        "category": "HR & Recruiting",
        "models": ["DeepSeek"],
        "prompt_count": 6,
        "price": 180000,
        "verified": True,
        "verify": "originality",
        "tags": ["Hiring", "AI interviewer", "RAG"],
        "metrics": [
            {"label": "Trial turns", "value": "8"},
            {"label": "Max questions", "value": "6"},
            {"label": "Human review", "value": "Required"},
        ],
        "prompt_text": (
            "You are the Mworks AI Interviewer. You are an AI. Never claim to be a human.\n"
            "Ask one question at a time about automation, testing, and secrets handling.\n"
            "Ground answers in the candidate Mworks profile, a short CV excerpt, and company documents.\n"
            "Do not execute code. Do not make a hire decision. Return a scorecard for a human reviewer."
        ),
        "seller_email": "labs@mworks.ng",
        "seller_name": "Mworks Labs",
        "trust": 94,
        "sales": 18,
        "rating": 4.8,
        "reviews_n": 9,
        "reviews": [{"author": "Kemi Adeyemi", "stars": 5, "text": "We trialled it on two RPA roles before buying seats."}],
    },
]


def _pack_markdown(item: dict) -> str:
    return (
        f"# {item['title']}\n\n"
        f"{item['description']}\n\n"
        "## How to use\n"
        "1. Duplicate this pack for your engagement.\n"
        "2. Fill the highlighted fields. Do not paste client names or production data.\n"
        "3. Walk the workshop with this as the shared canvas.\n\n"
        "## Fields\n"
        "- Process name\n"
        "- Volume per week\n"
        "- Exception rate\n"
        "- Systems touched\n"
        "- Build, buy, or skip\n"
    )


def _attach_catalog_files(db: Session, settings: Settings) -> None:
    by_slug = {item["slug"]: item for item in CATALOG}
    rows = db.query(Listing).filter(Listing.slug.in_(list(by_slug))).all()
    changed = False
    for row in rows:
        item = by_slug[row.slug]
        seller = row.seller or db.query(User).filter(User.id == row.seller_id).one_or_none()
        if seller is None:
            continue
        if item.get("prompt_text") and not (row.prompt_body or "").strip():
            row.prompt_body = item["prompt_text"]
            changed = True
        if row.type == "document" and not row.object_key:
            key = f"document/{seller.public_id}/seed-{row.slug}.md"
            body = _pack_markdown(item).encode("utf-8")
            if put_bytes(settings, key=key, body=body, content_type="text/markdown"):
                row.object_key = key
                changed = True
    if changed:
        db.commit()


def seed(db: Session, settings: Settings) -> None:
    demo = db.query(User).filter(User.email == settings.DEMO_USER_EMAIL.lower()).one_or_none()
    if demo is None:
        demo = User(
            email=settings.DEMO_USER_EMAIL.lower(),
            name="Henry Okafor",
            role="both",
            password_hash=hash_password(settings.DEMO_USER_PASSWORD),
            trust_score=93,
            sales_count=6,
            rating=4.8,
            review_count=5,
            country="Nigeria",
            is_admin=True,
        )
        db.add(demo)
        db.flush()
        log.info("seeded demo user %s", demo.email)
    elif settings.APP_ENV == "local":
        demo.is_admin = True

    for item in CATALOG:
        if db.query(Listing).filter(Listing.slug == item["slug"]).one_or_none():
            continue
        seller = _seller(
            db,
            item["seller_email"],
            item["seller_name"],
            item["trust"],
            item["sales"],
            item["rating"],
            item["reviews_n"],
            settings.DEMO_USER_PASSWORD,
        )
        db.add(
            Listing(
                slug=item["slug"],
                seller_id=seller.id,
                type=item["type"],
                title=item["title"],
                blurb=item["blurb"],
                description=item["description"],
                category=item["category"],
                platform=item.get("platform"),
                models=item.get("models") or [],
                prompt_count=item.get("prompt_count"),
                price_value=item["price"],
                rating=item["rating"],
                review_count=item["reviews_n"],
                verified=item["verified"],
                verify_type=item["verify"],
                delivery="Instant download" if item["type"] in {"prompt", "document", "agent"} else "1-3 days setup",
                tags=item["tags"],
                metrics=item.get("metrics") or [],
                verification_log=[{"label": "Seed import", "status": "Passed"}],
                reviews=item.get("reviews") or [],
                license=item.get("license"),
                prompt_body=item.get("prompt_text"),
                status="live",
            )
        )
    db.commit()
    _attach_catalog_files(db, settings)
    _seed_jobs(db, settings)
    _seed_messages(db, demo, settings)
    _seed_blog(db, demo)


BLOG_POSTS = [
    {
        "slug": "welcome-to-the-mworks-blog",
        "title": "Welcome to the Mworks blog",
        "excerpt": "News, playbooks, and honest lessons from the people building automation and AI work across Africa.",
        "category": "Announcements",
        "tags": ["Mworks", "Community"],
        "read_minutes": 2,
        "cover": "/keyboard-hero.jpg",
        "body": (
            "Mworks started with a simple idea: proof beats promises. Every automation on the marketplace "
            "earns its badge in a sandbox, every document pack passes an originality check, and every "
            "AI interviewer says out loud that it is an AI.\n\n"
            "This blog carries that same spirit. Expect practical playbooks from sellers who ship, "
            "plain-English coverage of the AI news that actually matters here, and behind-the-scenes notes "
            "on how we build the platform.\n\n"
            "Some posts are drafted by our newsroom agent from public tech feeds. "
            "They go live as soon as they are written, always with a source link, "
            "and they say so at the top when they are AI-assisted."
        ),
    },
    {
        "slug": "five-signs-a-process-is-ready-for-automation",
        "title": "Five signs a process is ready for automation",
        "excerpt": "Not every messy workflow needs a bot. Here is the checklist our top sellers use before they quote a client.",
        "category": "Playbooks",
        "tags": ["RPA", "Playbooks"],
        "read_minutes": 4,
        "body": (
            "The fastest way to lose money on automation is to automate the wrong thing. Before our top "
            "sellers quote a client, they run the process through five questions.\n\n"
            "## 1. Is it rule-based?\n\n"
            "If a human can write the decision as a flowchart, a bot can follow it. If every case needs "
            "judgement, you want a human in the loop, not a script.\n\n"
            "## 2. Does it repeat?\n\n"
            "A reconciliation that runs every night pays for itself. A report someone builds twice a year "
            "does not.\n\n"
            "## 3. Is the input digital and stable?\n\n"
            "Bots break when the bank changes its statement layout. Ask how often the inputs change before "
            "you promise uptime.\n\n"
            "## 4. Can you measure the saving?\n\n"
            "Count the hours, multiply by the salary, and put the number in the proposal. Buyers on Mworks "
            "trust metrics, not adjectives.\n\n"
            "## 5. Is there a fallback?\n\n"
            "Every good automation ships with a plan for the day it fails. If a missed run costs real money, "
            "build the alert before you build the bot."
        ),
    },
    {
        "slug": "how-the-ai-interviewer-screens-fairly",
        "title": "How the Mworks AI interviewer screens fairly",
        "excerpt": "The agent asks the questions, but a human always makes the call. Here is exactly how a screening session works.",
        "category": "Product",
        "tags": ["AI interviewer", "Hiring"],
        "read_minutes": 3,
        "body": (
            "Companies on Mworks can trial, buy, or hire an AI interviewer to run first-round developer "
            "screens. Because hiring is high-stakes, the guardrails matter more than the model.\n\n"
            "Every session starts with a disclosure: the candidate is told they are talking to an AI, and "
            "nothing happens until they consent. The agent asks a capped number of questions built from the "
            "job description, the candidate's profile, and any docs the company uploaded.\n\n"
            "At the end, the agent writes a scorecard with evidence for each rating. That scorecard lands on "
            "the application for a human reviewer. The agent never rejects anyone and never makes a hire "
            "decision. It saves the humans time; it does not replace their judgement."
        ),
    },
]


def _seed_blog(db: Session, demo: User | None) -> None:
    for item in BLOG_POSTS:
        cover = item.get("cover")
        row = db.query(BlogPost).filter(BlogPost.slug == item["slug"]).one_or_none()
        if row is None:
            db.add(
                BlogPost(
                    slug=item["slug"],
                    title=item["title"],
                    excerpt=item["excerpt"],
                    body=item["body"],
                    category=item["category"],
                    tags=item["tags"],
                    source="manual",
                    author_id=demo.id if demo else None,
                    status="published",
                    cover_url=cover,
                    media=[{"kind": "image", "url": cover}] if cover else [],
                    read_minutes=item["read_minutes"],
                    published_at=datetime.now(timezone.utc),
                )
            )
        elif cover and not row.cover_url:
            row.cover_url = cover
            row.media = [{"kind": "image", "url": cover}]
    now = datetime.now(timezone.utc)
    for row in db.query(BlogPost).filter(BlogPost.source == "agent", BlogPost.status == "draft"):
        row.status = "published"
        if row.published_at is None:
            row.published_at = now
    db.commit()


def _seed_jobs(db: Session, settings: Settings) -> None:
    by_slug: dict[str, Job] = {}
    for item in JOBS:
        row = db.query(Job).filter(Job.slug == item["slug"]).one_or_none()
        if row is None:
            poster = _seller(
                db,
                item["poster_email"],
                item["poster_name"],
                88,
                0,
                0.0,
                0,
                settings.DEMO_USER_PASSWORD,
            )
            row = Job(
                slug=item["slug"],
                poster_id=poster.id,
                title=item["title"],
                company=item["company"],
                company_avatar=item["company_avatar"],
                verified_employer=True,
                track=item["track"],
                type=item["type"],
                location=item["location"],
                salary=item["salary"],
                salary_min=item["salary_min"],
                min_trust=item["min_trust"],
                skills=item["skills"],
                about=item["about"],
                description=item["description"],
                responsibilities=item["responsibilities"],
                applicant_count=item["applicants"],
                status="live",
                created_at=job_created_at(item["age_days"]),
            )
            db.add(row)
            db.flush()
        by_slug[item["slug"]] = row
    db.commit()

    henry = db.query(User).filter(User.email == settings.DEMO_USER_EMAIL.lower()).one_or_none()
    if henry is None:
        return
    pref = db.query(AgentPref).filter(AgentPref.user_id == henry.id).one_or_none()
    if pref is None:
        db.add(AgentPref(user_id=henry.id, enabled=True, threshold=85, dismissed=[]))
    for item in HENRY_APPLICATIONS:
        job = by_slug.get(item["slug"])
        if job is None:
            continue
        exists = (
            db.query(JobApplication)
            .filter(JobApplication.job_id == job.id, JobApplication.applicant_id == henry.id)
            .one_or_none()
        )
        if exists:
            continue
        db.add(
            JobApplication(
                job_id=job.id,
                applicant_id=henry.id,
                via=item["via"],
                fit=item["fit"],
                status=item["status"],
                share_history=True,
                created_at=job_created_at(item["age_days"]),
            )
        )
    db.commit()


def _pair_users(a: User, b: User) -> tuple[str, str]:
    return (a.id, b.id) if a.id < b.id else (b.id, a.id)


def _seed_messages(db: Session, henry: User, settings: Settings) -> None:
    if henry is None:
        return
    threads = [
        (
            "abdul@mworks.ng",
            "Abdul R.",
            [
                ("them", "The invoice bot sandbox run finished clean. Want the exception-mapping notes?"),
                ("me", "Yes - send the mapping and I will review tonight."),
            ],
        ),
        (
            "semicolon@mworks.ng",
            "Semicolon Africa",
            [
                ("them", "Cohort 13 applications open next week"),
                ("me", "Send the showcase list when it is ready."),
            ],
        ),
        (
            "kudi@mworks.ng",
            "Fintech Ops (Employer)",
            [
                ("them", "Can you hop on a call Thursday?"),
            ],
        ),
        (
            "tolu@mworks.ng",
            "Tolu O.",
            [
                ("them", "Thanks for the review!"),
                ("me", "Anytime - the triage pack is solid."),
            ],
        ),
    ]
    for email, name, lines in threads:
        other = db.query(User).filter(User.email == email).one_or_none()
        if other is None:
            other = _seller(db, email, name, 80, 0, 0.0, 0, settings.DEMO_USER_PASSWORD)
        a_id, b_id = _pair_users(henry, other)
        conv = (
            db.query(Conversation)
            .filter(Conversation.user_a_id == a_id, Conversation.user_b_id == b_id)
            .one_or_none()
        )
        if conv is None:
            conv = Conversation(user_a_id=a_id, user_b_id=b_id)
            db.add(conv)
            db.flush()
        if db.query(ChatMessage).filter(ChatMessage.conversation_id == conv.id).first():
            continue
        for who, body in lines:
            sender = henry if who == "me" else other
            db.add(ChatMessage(conversation_id=conv.id, sender_id=sender.id, body=body))
    db.commit()
