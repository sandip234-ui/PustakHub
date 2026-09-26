"""
PustakHub — Demo Data & Seed Subsystem (Phase 11).

Provides deterministic, realistic, production-safe demo data seeding for:
  - Categories (20 academic/technical domains)
  - Books (500 realistic books with valid ISBN-13 check digits)
  - Book Copies (~1,200+ physical copies with barcodes and shelf locations)
  - Demo Users (ADMIN, LIBRARIAN, STUDENT, GUEST with Argon2id hashed passwords)
  - Borrow Records (100 borrowing records: active, overdue, returned)
  - Fines (Automated overdue penalties linked 1:1 with late returns)

SECURITY & SAFETY:
  - Refuses to run against production unless explicitly forced with --force-production-seed.
  - Never automatically executed at application startup.
  - Idempotent: re-running does not create duplicate entries.
  - Reset command (--reset-demo) safely removes only demo-tagged records.
"""

import argparse
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models import (
    AccountStatus,
    Book,
    BookCopy,
    BorrowRecord,
    BorrowStatus,
    Category,
    CopyStatus,
    Fine,
    FineReason,
    FineStatus,
    Role,
    User,
)
from app.modules.permissions.service import permission_service

logger = get_logger(__name__)

# Default deterministic random seed
DEFAULT_RANDOM_SEED = 20260924

# Fixed reference date for deterministic timestamp generation
REFERENCE_DATE = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)

# Demo User Email Domain
DEMO_EMAIL_DOMAIN = "@pustakhub.com"

# Demo User Credentials (Development Only)
DEMO_PASSWORDS = {
    "ADMIN": os.getenv("DEMO_ADMIN_PASSWORD", "PustakHubDemo!2026#Admin"),
    "LIBRARIAN": os.getenv("DEMO_LIBRARIAN_PASSWORD", "PustakHubDemo!2026#Library"),
    "STUDENT": os.getenv("DEMO_STUDENT_PASSWORD", "PustakHubDemo!2026#Student"),
    "GUEST": os.getenv("DEMO_GUEST_PASSWORD", "PustakHubDemo!2026#Guest"),
}

# ---------------------------------------------------------------------------
# 1. Categories Definition (20 Domains)
# ---------------------------------------------------------------------------

DEMO_CATEGORIES = [
    {
        "name": "Computer Science & Theory",
        "description": "Foundations of computational models, automata theory, and computational complexity.",
    },
    {
        "name": "Artificial Intelligence",
        "description": "Search algorithms, knowledge representation, expert systems, and autonomous agents.",
    },
    {
        "name": "Machine Learning & Deep Learning",
        "description": "Statistical learning, neural network architectures, optimization, and generative models.",
    },
    {
        "name": "Data Science & Big Data",
        "description": "Data analytics, distributed processing pipelines, ETL architecture, and visualization.",
    },
    {
        "name": "Database Systems & Storage",
        "description": "Relational query engines, NoSQL architectures, distributed storage, and indexing internals.",
    },
    {
        "name": "Operating Systems & Kernel",
        "description": "Kernel architecture, process scheduling, memory virtualization, and device drivers.",
    },
    {
        "name": "Computer Networks & Cloud",
        "description": "TCP/IP protocols, software-defined networking, microservice communication, and cloud infrastructure.",
    },
    {
        "name": "Cybersecurity & Cryptography",
        "description": "Applied cryptography, network security, penetration testing, IAM, and zero-trust engineering.",
    },
    {
        "name": "Software Engineering & Architecture",
        "description": "Design patterns, domain-driven design, clean architecture, and distributed systems design.",
    },
    {
        "name": "Web Development & Frontend",
        "description": "Modern full-stack web architectures, reactive client frameworks, and API engineering.",
    },
    {
        "name": "Algorithms & Data Structures",
        "description": "Advanced tree structures, graph algorithms, dynamic programming, and amortized analysis.",
    },
    {
        "name": "Mathematics & Discrete Structures",
        "description": "Linear algebra, discrete mathematics, graph theory, probability, and numerical methods.",
    },
    {
        "name": "Quantum Computing & Physics",
        "description": "Quantum algorithms, quantum cryptography, quantum circuits, and statistical mechanics.",
    },
    {
        "name": "DevOps & Reliability Engineering",
        "description": "Continuous delivery pipelines, container orchestration, telemetry, and site reliability.",
    },
    {
        "name": "Business Strategy & Technology",
        "description": "Product management, technology leadership, organizational engineering, and SaaS economics.",
    },
    {
        "name": "Economics & Financial Technology",
        "description": "Quantitative finance, algorithmic trading, decentralized ledger technology, and macroeconomic systems.",
    },
    {
        "name": "Cognitive Science & HCI",
        "description": "Human-computer interaction, usability engineering, cognitive ergonomics, and user experience.",
    },
    {
        "name": "Philosophy of Technology & Ethics",
        "description": "AI safety, tech ethics, digital rights, privacy engineering, and the sociology of computing.",
    },
    {
        "name": "History of Computing",
        "description": "Historical evolution of computational hardware, programming languages, and Internet protocols.",
    },
    {
        "name": "Bioinformatics & Genomics",
        "description": "Computational genomics, sequence alignment, protein folding algorithms, and structural biology.",
    },
]

# ---------------------------------------------------------------------------
# 2. Book Metadata Pools & Generators
# ---------------------------------------------------------------------------

AUTHORS_POOL = [
    "Dr. Vikram Patel",
    "Elena Rostova",
    "Prof. Arjun Mehta",
    "Sarah Jenkins",
    "Daniel Carter",
    "Priya Sharma",
    "Dr. Marcus Vance",
    "Rohan Patel",
    "Maya Rao",
    "David K. Chen",
    "Dr. Ananya Verma",
    "Michael Thorne",
    "Dr. Li Wei",
    "Aarav Gupta",
    "Prof. Catherine Dubois",
    "Naveen Sen",
    "Kavita Deshmukh",
    "Prof. Alexander Wright",
    "Sofia Lindqvist",
    "Rajesh Mukherjee",
]

PUBLISHERS_POOL = [
    "Northstar Academic Press",
    "Open Systems Publishing",
    "Pustak Academic House",
    "TechBridge Press",
    "KnowledgeWorks Publishing",
    "Algorithmic Press",
    "Vanguard Computing Books",
    "Beacon Scientific Press",
    "Apex Technical Publishing",
    "Matrix Educational Media",
]

# Title generation templates per category
CATEGORY_TITLE_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    "Computer Science & Theory": [
        ("Foundations of Computational Complexity", "Rigorous introduction to Turing machines, P vs NP, and reduction techniques."),
        ("Automata Theory and Formal Languages", "Comprehensive study of regular grammars, pushdown automata, and decidability."),
        ("Modern Computational Models", "Exploration of cellular automata, lambda calculus, and non-deterministic machines."),
        ("Logic in Computer Science", "Propositional logic, predicate calculus, and automated theorem proving."),
        ("Advanced Computability Theory", "Recursion theory, Turing degrees, and arithmetic hierarchy in modern computing."),
    ],
    "Artificial Intelligence": [
        ("Principles of Autonomous Agents", "Designing intelligent agents, decision-theoretic planning, and multi-agent coordination."),
        ("Knowledge Representation and Reasoning", "Ontologies, semantic networks, description logics, and probabilistic reasoning."),
        ("Heuristic Search and Problem Solving", "A* search, minimax game trees, alpha-beta pruning, and constraint satisfaction."),
        ("Symbolic Artificial Intelligence", "Rule-based expert systems and declarative knowledge modeling."),
        ("Applied Natural Language Understanding", "Syntax parsing, semantic parsing, and discourse representation models."),
    ],
    "Machine Learning & Deep Learning": [
        ("Statistical Foundations of Machine Learning", "PAC learning, bias-variance tradeoff, and kernel methods."),
        ("Deep Learning Architectures at Scale", "Convolutional networks, Transformers, residual connections, and attention mechanisms."),
        ("Reinforcement Learning in Practice", "Markov decision processes, Q-learning, policy gradients, and actor-critic algorithms."),
        ("Probabilistic Graphical Models", "Bayesian networks, Markov random fields, and variational inference algorithms."),
        ("Generative Diffusion Models", "Mathematics of score-based diffusion, denoising autoencoders, and sampling dynamics."),
    ],
    "Data Science & Big Data": [
        ("Distributed Stream Processing", "Real-time stream processing with exactly-once delivery guarantees and windowing."),
        ("Massive Data Analytics with MapReduce", "Algorithms for massive datasets, locality-sensitive hashing, and map-reduce patterns."),
        ("Modern Feature Engineering", "Techniques for tabular, textual, and temporal feature extraction and selection."),
        ("Data Pipeline Architecture and Governance", "Building resilient ETL pipelines, lineage tracking, and schema migration systems."),
        ("Statistical Data Mining", "Association rule learning, clustering techniques, and anomaly detection algorithms."),
    ],
    "Database Systems & Storage": [
        ("Database Engine Internals: Storage and Indexing", "B+ Trees, LSM-Trees, write-ahead logging, and buffer pool architectures."),
        ("Distributed Transactions and Consensus", "Two-phase commit, Paxos, Raft, and multi-version concurrency control in distributed databases."),
        ("Modern Query Optimization", "Cost-based query optimizers, relational algebra transformations, and columnar vectorized execution."),
        ("NoSQL Architecture: Key-Value, Document, and Graph", "CAP theorem trade-offs, consistent hashing, and document index design."),
        ("High-Performance SQL Processing", "Concurrency control, latch-free data structures, and in-memory transactional processing."),
    ],
    "Operating Systems & Kernel": [
        ("Operating System Architecture: Concepts and Internals", "Kernel design, preemptive multitasking, interrupt handling, and virtual memory paging."),
        ("Linux Kernel Development Guide", "Device drivers, process management, slab allocators, and kernel synchronization primitives."),
        ("Concurrent and Systems Programming", "POSIX threads, memory barriers, lock-free queues, and asynchronous I/O architectures."),
        ("Real-Time Operating Systems for Embedded Devices", "Deterministic scheduling, priority inversion solutions, and microkernel architectures."),
        ("Memory Management in Modern Operating Systems", "Virtual memory subsystem, page replacement algorithms, and NUMA architectures."),
    ],
    "Computer Networks & Cloud": [
        ("High-Performance TCP/IP Networking", "Congestion control algorithms, socket programming, zero-copy I/O, and protocol design."),
        ("Software-Defined Networking and Programmable Planes", "OpenFlow architecture, P4 programmable switches, and virtual overlay networks."),
        ("Cloud Infrastructure and Distributed Systems", "Hypervisors, container primitives, service mesh architectures, and control planes."),
        ("Modern Internet Protocol Engineering", "QUIC, HTTP/3, BGP routing protocols, and global content delivery networks."),
        ("Wireless and Mobile Communication Systems", "Cellular protocol stacks, wireless MAC layers, and multi-path TCP."),
    ],
    "Cybersecurity & Cryptography": [
        ("Applied Cryptography: Protocols and Primitives", "Symmetric block ciphers, authenticated encryption (AEAD), RSA, and elliptic curve cryptography."),
        ("Zero Trust Architecture and Identity Management", "Continuous authentication, resource-level authorization, and mutual TLS frameworks."),
        ("Network Security and Penetration Testing", "Threat modeling, packet analysis, vulnerability scanning, and defense-in-depth design."),
        ("Modern Application Security and Secure Coding", "Defending against injection attacks, cross-site vulnerabilities, IDOR, and memory corruptions."),
        ("Security Operations and Incident Response", "SIEM architecture, log analysis, threat hunting, and digital forensics methodology."),
    ],
    "Software Engineering & Architecture": [
        ("Designing Resilient Distributed Systems", "Circuit breakers, bulkhead patterns, rate limiting, and fault-tolerant architecture."),
        ("Domain-Driven Design and Clean Architecture", "Strategic and tactical DDD, bounded contexts, entities, aggregates, and clean layer separation."),
        ("Microservices Patterns and Anti-Patterns", "Saga orchestration, event-driven choreography, API gateways, and distributed tracing."),
        ("Refactoring and Technical Debt Management", "Transforming monolithic codebases into modular, testable, and maintainable architectures."),
        ("Software Testing Strategies: TDD to Property Testing", "Unit testing, integration testing, property-based testing, and mutation coverage."),
    ],
    "Web Development & Frontend": [
        ("Modern Web Application Architecture", "Single-page applications, server-side rendering, hydration algorithms, and client state."),
        ("Reactive UI Patterns and State Management", "Signals, virtual DOM reconcilers, immutable state pipelines, and component composition."),
        ("Scalable RESTful and GraphQL API Design", "Schema design, pagination, idempotency keys, rate limiting, and HTTP cache headers."),
        ("Browser Runtime Internals and Performance", "Event loop mechanics, critical rendering path optimization, and memory profiling."),
        ("Progressive Web Applications and Offline Systems", "Service workers, Cache API, background synchronization, and local storage engines."),
    ],
    "Algorithms & Data Structures": [
        ("Advanced Algorithms: Design and Analysis", "Greedy strategies, divide-and-conquer, dynamic programming, and linear programming."),
        ("Data Structures for High-Throughput Systems", "Skip lists, Bloom filters, Trie structures, and lock-free concurrent hash maps."),
        ("Graph Algorithms and Network Flow", "Shortest path algorithms, maximum flow, minimum cut, and bipartite matching."),
        ("Approximation and Randomized Algorithms", "NP-hard optimization heuristics, Monte Carlo methods, and randomized data structures."),
        ("Computational Geometry: Algorithms and Applications", "Convex hulls, Voronoi diagrams, Delaunay triangulations, and spatial indexing."),
    ],
    "Mathematics & Discrete Structures": [
        ("Linear Algebra for Computing and Data Science", "Matrix decompositions, SVD, eigenvalues, eigenvectors, and vector spaces."),
        ("Discrete Mathematics for Computer Engineers", "Combinatorics, graph theory, modular arithmetic, and recurrence relations."),
        ("Probability and Stochastic Processes", "Markov chains, Poisson processes, random walks, and Bayesian inference."),
        ("Numerical Methods and Scientific Computing", "Floating-point error analysis, root-finding algorithms, and numerical integration."),
        ("Information Theory and Coding", "Shannon entropy, channel capacity, Huffman coding, and error-correcting codes."),
    ],
    "Quantum Computing & Physics": [
        ("Quantum Computing: Principles and Algorithms", "Qubits, quantum superposition, entanglement, Shor's algorithm, and Grover's search."),
        ("Quantum Circuit Design and Simulation", "Clifford gates, error mitigation, quantum teleportation, and Hamiltonian simulation."),
        ("Quantum Cryptography and Post-Quantum Security", "QKD protocols, BB84, lattice-based cryptography, and quantum-resistant algorithms."),
        ("Statistical Mechanics for Complex Systems", "Thermodynamic limits, phase transitions, and network entropy."),
        ("Introduction to Quantum Information Theory", "Density matrices, quantum state tomography, and entanglement quantification."),
    ],
    "DevOps & Reliability Engineering": [
        ("Site Reliability Engineering: Principles and Operations", "Service level objectives (SLOs), error budgets, blameless postmortems, and toil reduction."),
        ("Continuous Delivery and Infrastructure as Code", "Declarative infrastructure, GitOps workflows, automated canary deployments, and immutable servers."),
        ("Observability Engineering: Metrics, Logs, and Traces", "Distributed tracing with OpenTelemetry, Prometheus metric collection, and structured logging."),
        ("Container Orchestration with Kubernetes", "Control plane architecture, custom resource definitions (CRDs), and networking plugins."),
        ("Chaos Engineering and Resilience Testing", "Fault injection, resilience verification, and catastrophe modeling in distributed clouds."),
    ],
    "Business Strategy & Technology": [
        ("Technology Leadership and Engineering Management", "Team topology, technical roadmap design, high-performance engineering culture, and hiring."),
        ("Product Management for Scalable Platforms", "User research, feature prioritization frameworks, product telemetry, and go-to-market strategies."),
        ("Economics of Cloud Computing and SaaS", "Unit economics, cost optimization, multi-tenant pricing models, and cloud financial operations."),
        ("Platform Engineering and Developer Experience", "Internal developer platforms, self-service portals, reducing cognitive load, and CLI tooling."),
        ("Strategic Innovation in Software Enterprises", "Disruptive technology frameworks, architecture agility, and technological horizon planning."),
    ],
    "Economics & Financial Technology": [
        ("Algorithmic Trading Systems Architecture", "Order matching engines, low-latency market data feeds, and market making strategies."),
        ("Quantitative Risk Management and Modeling", "Value at Risk (VaR), stress testing, credit risk models, and liquidity analytics."),
        ("Decentralized Ledger Technology and Smart Contracts", "Consensus protocols, state machine replication, smart contract security, and cryptographic proofs."),
        ("Financial Data Engineering and Analytics", "Time-series database modeling, tick data processing, and backtesting frameworks."),
        ("Modern Banking Protocols and Payment Systems", "ISO 20022 messaging, clearinghouse settlement workflows, and payment gateway security."),
    ],
    "Cognitive Science & HCI": [
        ("Cognitive Foundations of User Interface Design", "Visual perception, mental models, Fitts's law, and reducing cognitive friction in interfaces."),
        ("Human-Computer Interaction: Principles and Methods", "Interaction design paradigms, contextual inquiries, and rigorous usability testing."),
        ("Accessibility Engineering and Inclusive Design", "WCAG guidelines, assistive technologies, semantic markup, and screen-reader compatibility."),
        ("Information Architecture and Visual Hierarchy", "Card sorting, site tree taxonomy, wayfinding systems, and responsive layout ergonomics."),
        ("Voice User Interfaces and Conversational Agents", "Dialogue management, speech act theory, and conversational user experience."),
    ],
    "Philosophy of Technology & Ethics": [
        ("Ethics of Artificial Intelligence and Autonomy", "Algorithmic bias, fairness metrics, explainability (XAI), and moral machine decision-making."),
        ("Privacy Engineering and Digital Rights", "Data sovereignty, differential privacy, zero-knowledge proofs, and regulatory frameworks."),
        ("Philosophy of Computing and Information", "The nature of computation, Church-Turing thesis philosophy, and simulation theory."),
        ("Technological Disruption and Society", "Impact of automation on labor markets, digital commons, and surveillance capitalism."),
        ("Open Source Governance and Digital Sustainability", "Collaborative development economics, open-source licensing models, and software maintenance ethics."),
    ],
    "History of Computing": [
        ("The Pioneers of Computing: From Babbage to Turing", "Mechanical computing engines, ENIAC, wartime codebreaking, and the birth of computer science."),
        ("Evolution of Programming Languages", "From Assembly to Fortran, Lisp, C, and modern memory-safe languages (Rust, Go)."),
        ("History of the Internet and Open Protocols", "ARPANET, TCP/IP RFC evolution, the invention of the World Wide Web, and browser wars."),
        ("The Microprocessor Revolution: Silicon to SoC", "Integrated circuits, Moore's law progression, x86 vs ARM architectures, and RISC-V."),
        ("Milestones in Operating System History", "Unix philosophy, Multics, BSD, the creation of Linux, and the open-source movement."),
    ],
    "Bioinformatics & Genomics": [
        ("Computational Genomics and Sequence Analysis", "Sequence alignment algorithms (Smith-Waterman, BLAST), hidden Markov models, and genome assembly."),
        ("Structural Bioinformatics and Protein Modeling", "AlphaFold architectures, 3D coordinate analysis, molecular dynamics simulations, and binding site prediction."),
        ("Phylogenetics and Evolutionary Trees", "Maximum parsimony, neighbor-joining, maximum likelihood, and molecular clock estimation."),
        ("Biomedical Ontologies and Knowledge Graphs", "EMBL-EBI OLS, Gene Ontology (GO), disease annotations, and biomedical semantic web."),
        ("Systems Biology and Metabolic Network Modeling", "Flux balance analysis, cellular signaling pathways, and mathematical modeling of biochemical networks."),
    ],
}

# ---------------------------------------------------------------------------
# 3. Helper Functions (ISBN, Determinism, Status Helpers)
# ---------------------------------------------------------------------------

def calculate_isbn13(seed_int: int) -> str:
    """
    Generate a deterministic, mathematically valid ISBN-13 with check digit.
    Format: 978-X-XXXX-XXXX-C
    """
    base_9 = f"{seed_int:09d}"
    digits = [9, 7, 8] + [int(d) for d in base_9]
    # ISBN-13 check digit formula: alternate weights 1 and 3
    weighted_sum = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    check_digit = (10 - (weighted_sum % 10)) % 10
    raw = "".join(str(d) for d in digits) + str(check_digit)
    return f"{raw[:3]}-{raw[3]}-{raw[4:8]}-{raw[8:12]}-{raw[12]}"


def check_production_safety(force: bool = False) -> None:
    """Ensure seed script cannot accidentally execute in production."""
    env = getattr(settings, "ENVIRONMENT", "development").lower()
    if env == "production" and not force:
        msg = (
            "[SAFETY ERROR] Seeding demo data is blocked in production environment "
            "(ENVIRONMENT=production). To override for staging/demo environments, "
            "provide the --force-production-seed CLI flag."
        )
        logger.error(msg)
        raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# 4. Core Seeding Pipeline
# ---------------------------------------------------------------------------

def seed_categories(db: Session) -> List[Category]:
    """Seed the 20 standard library categories idempotently."""
    existing_cats = {c.name: c for c in db.query(Category).all()}
    categories = []

    for cat_data in DEMO_CATEGORIES:
        name = cat_data["name"]
        if name in existing_cats:
            cat = existing_cats[name]
            cat.description = cat_data["description"]
        else:
            cat = Category(
                id=uuid.uuid4(),
                name=name,
                description=cat_data["description"],
            )
            db.add(cat)
        categories.append(cat)

    db.flush()
    return categories


def seed_demo_users(db: Session) -> Dict[str, User]:
    """Seed dedicated demo users for each existing role."""
    # Ensure default roles exist in DB
    permission_service.seed_default_roles_and_permissions(db)
    roles = {r.name: r for r in db.query(Role).all()}

    user_specs = [
        ("admin.demo@pustakhub.com", "Demo Administrator", "ADMIN", DEMO_PASSWORDS["ADMIN"]),
        ("librarian.demo@pustakhub.com", "Demo Librarian", "LIBRARIAN", DEMO_PASSWORDS["LIBRARIAN"]),
        ("student.demo@pustakhub.com", "Demo Student", "STUDENT", DEMO_PASSWORDS["STUDENT"]),
        ("guest.demo@pustakhub.com", "Demo Guest", "GUEST", DEMO_PASSWORDS["GUEST"]),
        # Additional student accounts for rich circulation history
        ("student.aarav@pustakhub.com", "Aarav Sharma", "STUDENT", DEMO_PASSWORDS["STUDENT"]),
        ("student.diya@pustakhub.com", "Diya Patel", "STUDENT", DEMO_PASSWORDS["STUDENT"]),
        ("student.neha@pustakhub.com", "Neha Gupta", "STUDENT", DEMO_PASSWORDS["STUDENT"]),
        ("student.vikram@pustakhub.com", "Vikram Singh", "STUDENT", DEMO_PASSWORDS["STUDENT"]),
        ("student.ananya@pustakhub.com", "Ananya Verma", "STUDENT", DEMO_PASSWORDS["STUDENT"]),
    ]

    users = {}
    for email, full_name, role_name, raw_pwd in user_specs:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=email,
                full_name=full_name,
                password_hash=hash_password(raw_pwd),
                account_status=AccountStatus.ACTIVE,
                is_mfa_enabled=False,
            )
            if role_name in roles:
                user.roles.append(roles[role_name])
            db.add(user)
        else:
            # Update password and role if needed
            user.password_hash = hash_password(raw_pwd)
            user.account_status = AccountStatus.ACTIVE
            if role_name in roles and roles[role_name] not in user.roles:
                user.roles.append(roles[role_name])
        users[email] = user

    db.flush()
    return users


def seed_books(db: Session, categories: List[Category], seed_num: int = DEFAULT_RANDOM_SEED) -> List[Book]:
    """
    Deterministically generate exactly 500 books across the 20 categories (25 books per category).
    """
    rng = random.Random(seed_num)
    books: List[Book] = []

    # Check if demo books already exist
    existing_books = {b.isbn: b for b in db.query(Book).filter(Book.isbn.like("978-0-%")).all()}

    book_global_idx = 1
    for cat in categories:
        patterns = CATEGORY_TITLE_PATTERNS.get(cat.name, [
            ("Advanced Topics in " + cat.name, "Comprehensive technical coverage of core fundamentals.")
        ])

        # 25 books per category = 20 * 25 = 500 books exactly
        for i in range(25):
            isbn = calculate_isbn13(book_global_idx)
            base_title, base_desc = patterns[i % len(patterns)]
            
            # Formulate realistic book title variations
            edition_or_vol = ""
            if i >= len(patterns):
                variant_tags = [
                    f": Volume {i // len(patterns) + 1}",
                    f" (2nd Edition)",
                    f" (3rd Edition)",
                    f": Advanced Practitioner's Guide",
                    f": Theory and Implementation",
                ]
                edition_or_vol = variant_tags[(i // len(patterns) - 1) % len(variant_tags)]

            title = f"{base_title}{edition_or_vol}"
            author_count = rng.choice([1, 1, 2, 2, 3])
            selected_authors = rng.sample(AUTHORS_POOL, author_count)
            author = "; ".join(selected_authors)
            publisher = rng.choice(PUBLISHERS_POOL)
            publication_year = rng.randint(2005, 2026)
            description = (
                f"{base_desc} Explores state-of-the-art architectures, mathematical foundations, "
                f"and practical applications in {cat.name}."
            )

            if isbn in existing_books:
                book = existing_books[isbn]
                book.title = title
                book.author = author
                book.publisher = publisher
                book.publication_year = publication_year
                book.description = description
                book.category_id = cat.id
            else:
                book = Book(
                    id=uuid.uuid4(),
                    title=title,
                    author=author,
                    isbn=isbn,
                    publisher=publisher,
                    publication_year=publication_year,
                    description=description,
                    category_id=cat.id,
                )
                db.add(book)

            books.append(book)
            book_global_idx += 1

    db.flush()
    return books


def seed_book_copies(
    db: Session,
    books: List[Book],
    seed_num: int = DEFAULT_RANDOM_SEED
) -> List[BookCopy]:
    """
    Generate physical inventory copies for all books (~1,200+ copies).
    """
    rng = random.Random(seed_num + 1)
    existing_copies = {c.copy_identifier: c for c in db.query(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).all()}
    copies: List[BookCopy] = []

    for idx, book in enumerate(books, start=1):
        # 1 to 4 copies per book (deterministic average ~2.4 copies)
        num_copies = rng.choices([1, 2, 3, 4], weights=[15, 45, 30, 10])[0]
        
        for copy_idx in range(1, num_copies + 1):
            copy_identifier = f"PUSTAK-{idx:04d}-{copy_idx:02d}"
            shelf_row = chr(ord('A') + (idx % 8))
            shelf_col = (idx % 12) + 1
            shelf_loc = f"Bay-{shelf_row}{shelf_col}-Shelf{copy_idx}"

            # Default status AVAILABLE (borrow records will transition some to BORROWED)
            # A small fraction assigned to MAINTENANCE or LOST
            rand_val = rng.random()
            if rand_val < 0.05:
                status = CopyStatus.MAINTENANCE
            elif rand_val < 0.07:
                status = CopyStatus.LOST
            else:
                status = CopyStatus.AVAILABLE

            if copy_identifier in existing_copies:
                copy = existing_copies[copy_identifier]
                copy.book_id = book.id
                copy.shelf_location = shelf_loc
                # Only update status if not currently borrowed in an active loan
                if copy.status != CopyStatus.BORROWED:
                    copy.status = status
            else:
                copy = BookCopy(
                    id=uuid.uuid4(),
                    book_id=book.id,
                    copy_identifier=copy_identifier,
                    shelf_location=shelf_loc,
                    status=status,
                )
                db.add(copy)

            copies.append(copy)

    db.flush()
    return copies


def seed_borrow_records_and_fines(
    db: Session,
    copies: List[BookCopy],
    users: Dict[str, User],
    seed_num: int = DEFAULT_RANDOM_SEED
) -> Tuple[List[BorrowRecord], List[Fine]]:
    """
    Generate 100 realistic, internally consistent borrowing records and overdue fines.
    """
    rng = random.Random(seed_num + 2)
    
    # Filter available student users
    student_users = [
        u for email, u in users.items()
        if "student" in email and u.account_status == AccountStatus.ACTIVE
    ]
    if not student_users:
        logger.warning("No active student users available for borrow records.")
        return [], []

    # Get available copies for borrowing (filter out MAINTENANCE and LOST)
    borrowable_copies = [c for c in copies if c.status == CopyStatus.AVAILABLE]

    # Check for existing borrow records associated with demo copies
    existing_borrows = db.query(BorrowRecord).join(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).all()
    if existing_borrows:
        # If existing borrows exist, return them with their fines
        fines = db.query(Fine).join(BorrowRecord).join(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).all()
        return existing_borrows, fines

    borrow_records: List[BorrowRecord] = []
    fines: List[Fine] = []

    # We will generate exactly 100 borrow records:
    # 1. 25 Active on-time borrows (BorrowStatus.ACTIVE, BookCopy.status = BORROWED)
    # 2. 15 Active overdue borrows (BorrowStatus.OVERDUE, BookCopy.status = BORROWED)
    # 3. 45 Returned on-time records (BorrowStatus.RETURNED, BookCopy.status = AVAILABLE)
    # 4. 15 Returned late records with Fines (BorrowStatus.RETURNED, BookCopy.status = AVAILABLE, 1:1 Fine)

    used_copy_indices = set()

    def get_unused_copy(req_status: CopyStatus = CopyStatus.AVAILABLE) -> Optional[BookCopy]:
        for i, c in enumerate(borrowable_copies):
            if i not in used_copy_indices:
                used_copy_indices.add(i)
                c.status = req_status
                return c
        return None

    # Group 1: 25 Active On-Time
    for i in range(25):
        copy = get_unused_copy(CopyStatus.BORROWED)
        if not copy:
            break
        user = student_users[i % len(student_users)]
        issued_days_ago = rng.randint(2, 8)
        issued_at = REFERENCE_DATE - timedelta(days=issued_days_ago, hours=rng.randint(1, 10))
        due_at = issued_at + timedelta(days=14)

        record = BorrowRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            book_copy_id=copy.id,
            issued_at=issued_at,
            due_at=due_at,
            returned_at=None,
            status=BorrowStatus.ACTIVE,
        )
        db.add(record)
        borrow_records.append(record)

    # Group 2: 15 Active Overdue
    for i in range(15):
        copy = get_unused_copy(CopyStatus.BORROWED)
        if not copy:
            break
        user = student_users[(i + 2) % len(student_users)]
        issued_days_ago = rng.randint(18, 30)
        issued_at = REFERENCE_DATE - timedelta(days=issued_days_ago, hours=rng.randint(1, 10))
        due_at = issued_at + timedelta(days=14)  # Due between 4 and 16 days ago

        record = BorrowRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            book_copy_id=copy.id,
            issued_at=issued_at,
            due_at=due_at,
            returned_at=None,
            status=BorrowStatus.OVERDUE,
        )
        db.add(record)
        borrow_records.append(record)

    # Group 3: 45 Returned On-Time (Copy is back to AVAILABLE)
    for i in range(45):
        copy = get_unused_copy(CopyStatus.AVAILABLE)
        if not copy:
            break
        user = student_users[(i + 4) % len(student_users)]
        issued_days_ago = rng.randint(35, 90)
        issued_at = REFERENCE_DATE - timedelta(days=issued_days_ago, hours=rng.randint(1, 10))
        due_at = issued_at + timedelta(days=14)
        loan_duration = rng.randint(3, 13)  # returned before due
        returned_at = issued_at + timedelta(days=loan_duration, hours=rng.randint(1, 6))

        record = BorrowRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            book_copy_id=copy.id,
            issued_at=issued_at,
            due_at=due_at,
            returned_at=returned_at,
            status=BorrowStatus.RETURNED,
        )
        db.add(record)
        borrow_records.append(record)

    # Group 4: 15 Returned Late with Overdue Fines
    for i in range(15):
        copy = get_unused_copy(CopyStatus.AVAILABLE)
        if not copy:
            break
        user = student_users[(i + 1) % len(student_users)]
        issued_days_ago = rng.randint(40, 100)
        issued_at = REFERENCE_DATE - timedelta(days=issued_days_ago, hours=rng.randint(1, 10))
        due_at = issued_at + timedelta(days=14)
        overdue_days = rng.randint(2, 12)
        returned_at = due_at + timedelta(days=overdue_days, hours=rng.randint(1, 8))

        record = BorrowRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            book_copy_id=copy.id,
            issued_at=issued_at,
            due_at=due_at,
            returned_at=returned_at,
            status=BorrowStatus.RETURNED,
        )
        db.add(record)
        borrow_records.append(record)
        db.flush()

        # Generate corresponding Fine (1:1 with late BorrowRecord)
        fine_amount = Decimal(str(overdue_days * 2.00))
        fine_status = FineStatus.PAID if (i % 3 == 0) else FineStatus.PENDING

        fine = Fine(
            id=uuid.uuid4(),
            borrow_record_id=record.id,
            amount=fine_amount,
            reason=FineReason.OVERDUE,
            status=fine_status,
            notes=f"Overdue penalty: {overdue_days} days late @ $2.00/day.",
        )
        db.add(fine)
        fines.append(fine)

    db.flush()
    return borrow_records, fines


def reset_demo_data(db: Session, force: bool = False) -> Dict[str, int]:
    """
    Safely delete only demo-tagged records without dropping tables or altering production data.
    """
    check_production_safety(force=force)

    # 1. Delete Demo Fines
    fines_deleted = (
        db.query(Fine)
        .filter(Fine.borrow_record_id.in_(
            db.query(BorrowRecord.id)
            .join(BookCopy)
            .filter(BookCopy.copy_identifier.like("PUSTAK-%"))
        ))
        .delete(synchronize_session=False)
    )

    # 2. Delete Demo Borrow Records
    borrows_deleted = (
        db.query(BorrowRecord)
        .filter(BorrowRecord.book_copy_id.in_(
            db.query(BookCopy.id).filter(BookCopy.copy_identifier.like("PUSTAK-%"))
        ))
        .delete(synchronize_session=False)
    )

    # 3. Delete Demo Book Copies
    copies_deleted = (
        db.query(BookCopy)
        .filter(BookCopy.copy_identifier.like("PUSTAK-%"))
        .delete(synchronize_session=False)
    )

    # 4. Delete Demo Books
    books_deleted = (
        db.query(Book)
        .filter(Book.isbn.like("978-0-%"))
        .delete(synchronize_session=False)
    )

    # 5. Delete Demo Categories (only those in DEMO_CATEGORIES)
    cat_names = [c["name"] for c in DEMO_CATEGORIES]
    cats_deleted = (
        db.query(Category)
        .filter(Category.name.in_(cat_names))
        .delete(synchronize_session=False)
    )

    # 6. Delete Demo Users
    users_deleted = (
        db.query(User)
        .filter(User.email.like(f"%{DEMO_EMAIL_DOMAIN}"))
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "fines": fines_deleted,
        "borrow_records": borrows_deleted,
        "book_copies": copies_deleted,
        "books": books_deleted,
        "categories": cats_deleted,
        "demo_users": users_deleted,
    }


def seed_database(
    db: Session,
    seed_num: int = DEFAULT_RANDOM_SEED,
    force: bool = False
) -> Dict[str, int]:
    """
    Execute full deterministic demo seed pipeline.
    """
    check_production_safety(force=force)

    logger.info("Seeding categories...")
    categories = seed_categories(db)

    logger.info("Seeding demo users...")
    users = seed_demo_users(db)

    logger.info("Seeding 500 books...")
    books = seed_books(db, categories, seed_num=seed_num)

    logger.info("Seeding physical book copies...")
    copies = seed_book_copies(db, books, seed_num=seed_num)

    logger.info("Seeding borrowing records and overdue fines...")
    borrow_records, fines = seed_borrow_records_and_fines(db, copies, users, seed_num=seed_num)

    db.commit()

    return {
        "categories": len(categories),
        "demo_users": len(users),
        "books": len(books),
        "book_copies": len(copies),
        "borrow_records": len(borrow_records),
        "fines": len(fines),
    }


# ---------------------------------------------------------------------------
# 5. CLI Interface
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PustakHub — Safe, Deterministic Demo Data Seeding Subsystem (Phase 11)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--reset-demo",
        action="store_true",
        help="Safely remove all seeded demo data (books, copies, demo users, borrows, fines).",
    )
    parser.add_argument(
        "--seed-number",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help=f"Deterministic integer seed for RNG (default: {DEFAULT_RANDOM_SEED}).",
    )
    parser.add_argument(
        "--force-production-seed",
        action="store_true",
        help="Explicitly allow seeding/reset in ENVIRONMENT=production (use with caution).",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  PustakHub — Demo Data & Seed Subsystem (Phase 11)")
    print("=" * 60 + "\n")

    with SessionLocal() as db:
        if args.reset_demo:
            print("[RESET] Removing demo data...")
            result = reset_demo_data(db, force=args.force_production_seed)
            print("\nDemo Data Reset Complete:")
            print(f"  - Deleted Fines:          {result['fines']}")
            print(f"  - Deleted Borrow Records: {result['borrow_records']}")
            print(f"  - Deleted Book Copies:    {result['book_copies']}")
            print(f"  - Deleted Books:          {result['books']}")
            print(f"  - Deleted Categories:     {result['categories']}")
            print(f"  - Deleted Demo Users:     {result['demo_users']}")
            print("\n[STATUS] ✓ Demo data wiped cleanly.")
            return

        print(f"[SEED] Starting deterministic seeding with Seed = {args.seed_number}...")
        result = seed_database(db, seed_num=args.seed_number, force=args.force_production_seed)

        print("\n" + "─" * 45)
        print("  PustakHub Demo Data Seed Summary")
        print("─" * 45)
        print(f"  Categories:       {result['categories']:>5}")
        print(f"  Books:            {result['books']:>5}")
        print(f"  Book Copies:      {result['book_copies']:>5}")
        print(f"  Demo Users:       {result['demo_users']:>5}")
        print(f"  Borrow Records:   {result['borrow_records']:>5}")
        print(f"  Fines:            {result['fines']:>5}")
        print("─" * 45)
        print("\nDemo User Credentials (Development Only):")
        print("  • Admin:     admin.demo@pustakhub.com     / PustakHubDemo!2026#Admin")
        print("  • Librarian: librarian.demo@pustakhub.com / PustakHubDemo!2026#Library")
        print("  • Student:   student.demo@pustakhub.com   / PustakHubDemo!2026#Student")
        print("  • Guest:     guest.demo@pustakhub.com     / PustakHubDemo!2026#Guest")
        print("\n[STATUS] ✓ Seed completed successfully.\n")


if __name__ == "__main__":
    main()
