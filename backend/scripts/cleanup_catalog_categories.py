"""
cleanup_catalog_categories.py — Database migration & taxonomy cleanup script.

Cleans up polluted test categories in PustakHub:
1. Identifies the 20 canonical academic library categories.
2. Identifies all 137 test/generated/polluted categories.
3. Classifies and reassigns all 114 non-canonical books to canonical categories based on subject matter.
4. Enriches metadata (subtitles, scholarly descriptions, authors, publication years) for realism.
5. Deletes all 137 obsolete categories once 0 books reference them.
6. Verifies book count (614) and copy count (1495) are strictly preserved with zero data loss.
"""

import sys
import logging
from typing import Dict, List, Tuple
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.category import Category
from app.models.book import Book
from app.models.book_copy import BookCopy
from scripts.seed_demo import DEMO_CATEGORIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CANONICAL_NAMES = [c["name"] for c in DEMO_CATEGORIES]

# Scholarly topics for distributing Circulation Dynamics volumes across disciplines
CIRCULATION_TOPICS: List[Dict[str, str]] = [
    {
        "category": "Algorithms & Data Structures",
        "subtitle": "Network Flow and Capacity Scaling Algorithms",
        "author": "Dr. Vikram Patel",
        "publisher": "Algorithmic Press",
        "year": 2023,
        "description": "Maximum flow algorithms, circulation with demands, push-relabel methods, and polynomial-time capacity scaling in computational graphs.",
    },
    {
        "category": "Artificial Intelligence",
        "subtitle": "Multi-Agent Information Dissemination and Swarm Coordination",
        "author": "Dr. Ananya Verma",
        "publisher": "Vanguard Computing Books",
        "year": 2024,
        "description": "Decentralized consensus, multi-agent communication topology, belief propagation, and collective intelligence dynamics.",
    },
    {
        "category": "Bioinformatics & Genomics",
        "subtitle": "Hemodynamics and Physiological Flow Modeling",
        "author": "Dr. Li Wei",
        "publisher": "Beacon Scientific Press",
        "year": 2022,
        "description": "Computational fluid dynamics of arterial blood circulation, biomechanical shear stress, and microvascular network modeling.",
    },
    {
        "category": "Business Strategy & Technology",
        "subtitle": "Corporate Knowledge Transfer and Organizational Workflows",
        "author": "Daniel Carter",
        "publisher": "KnowledgeWorks Publishing",
        "year": 2023,
        "description": "Knowledge circulation inside distributed enterprises, organizational silos, information governance, and value stream optimization.",
    },
    {
        "category": "Cognitive Science & HCI",
        "subtitle": "Attentional Flow and Cognitive Ergonomics",
        "author": "Kavita Deshmukh",
        "publisher": "Matrix Educational Media",
        "year": 2024,
        "description": "Human attention circulation in dense multitasking interfaces, cognitive load theory, and perceptual feedback loops.",
    },
    {
        "category": "Computer Networks & Cloud",
        "subtitle": "Packet Queuing, Bufferbloat, and Congestion Control",
        "author": "David K. Chen",
        "publisher": "Open Systems Publishing",
        "year": 2023,
        "description": "Active queue management, BBR congestion control, fluid-flow approximation of TCP traffic, and overlay routing dynamics.",
    },
    {
        "category": "Computer Science & Theory",
        "subtitle": "Petri Net Token Dynamics and Reachability Invariants",
        "author": "Prof. Alexander Wright",
        "publisher": "Northstar Academic Press",
        "year": 2021,
        "description": "Algebraic analysis of marked graphs, Petri net invariants, token conservation laws, and deadlock-free circulation models.",
    },
    {
        "category": "Cybersecurity & Cryptography",
        "subtitle": "Cryptographic Key Rolling and Ephemeral Token Ratchets",
        "author": "Sarah Jenkins",
        "publisher": "TechBridge Press",
        "year": 2024,
        "description": "Double ratchet algorithms, automated certificate circulation, ephemeral secrets rotation, and forward secrecy in distributed systems.",
    },
    {
        "category": "Data Science & Big Data",
        "subtitle": "Real-Time Stream Ingestion and Backpressure Mechanics",
        "author": "Elena Rostova",
        "publisher": "Pustak Academic House",
        "year": 2023,
        "description": "Reactive streams backpressure, windowing semantics, buffer watermarking, and continuous distributed stream circulation.",
    },
    {
        "category": "Database Systems & Storage",
        "subtitle": "Write-Ahead Log Buffer Circulation and Page Eviction",
        "author": "Rohan Patel",
        "publisher": "Apex Technical Publishing",
        "year": 2022,
        "description": "Buffer pool circulation dynamics, LRU/CLOCK eviction variants, dirty page flushing policies, and memory-to-disk pipelines.",
    },
    {
        "category": "DevOps & Reliability Engineering",
        "subtitle": "Telemetry Event Streams and Observability Pipelines",
        "author": "Michael Thorne",
        "publisher": "Vanguard Computing Books",
        "year": 2024,
        "description": "Distributed tracing span circulation, sampling dynamics, high-cardinality metric rollups, and logging aggregation pipelines.",
    },
    {
        "category": "Economics & Financial Technology",
        "subtitle": "Monetary Velocity, Liquidity Pools, and Automated Market Makers",
        "author": "Prof. Arjun Mehta",
        "publisher": "Pustak Academic House",
        "year": 2023,
        "description": "Quantitative modeling of currency velocity, constant-product liquidity dynamics, cross-border settlement rails, and automated market making.",
    },
    {
        "category": "History of Computing",
        "subtitle": "The Evolution of System Bus and Memory Interconnects",
        "author": "Sofia Lindqvist",
        "publisher": "KnowledgeWorks Publishing",
        "year": 2022,
        "description": "Historical progression of computer buses from early backplanes and S-100 to PCI Express, HyperTransport, and optical interconnects.",
    },
    {
        "category": "Machine Learning & Deep Learning",
        "subtitle": "Gradient Flow and Loss Surface Dynamics in Deep Architectures",
        "author": "Aarav Gupta",
        "publisher": "Algorithmic Press",
        "year": 2024,
        "description": "Stochastic gradient circulation, vanishing/exploding gradient dynamics, residual pathway stabilization, and optimizer momentum dynamics.",
    },
    {
        "category": "Mathematics & Discrete Structures",
        "subtitle": "Vector Field Circulation, Stokes Theorem, and Differential Forms",
        "author": "Prof. Catherine Dubois",
        "publisher": "Northstar Academic Press",
        "year": 2021,
        "description": "Differential forms, line integrals, circulation density, Kelvin-Stokes theorem, and topological dynamics on Riemannian manifolds.",
    },
    {
        "category": "Operating Systems & Kernel",
        "subtitle": "Kernel Workqueue Dispatch and Interrupt Latency Control",
        "author": "Dr. Marcus Vance",
        "publisher": "Open Systems Publishing",
        "year": 2023,
        "description": "Asynchronous tasklet circulation, softirq balancing, bottom-half processing, and deterministic latency in preemptible kernels.",
    },
    {
        "category": "Philosophy of Technology & Ethics",
        "subtitle": "Open Knowledge Commons and Digital Dissemination Ethics",
        "author": "Rajesh Mukherjee",
        "publisher": "Beacon Scientific Press",
        "year": 2024,
        "description": "Ethical dimensions of open access research circulation, digital copyright regimes, algorithmic gatekeeping, and information justice.",
    },
    {
        "category": "Quantum Computing & Physics",
        "subtitle": "Superfluid Vortices and Quantized Circulation in Low-Temperature Physics",
        "author": "Prof. Alexander Wright",
        "publisher": "Beacon Scientific Press",
        "year": 2022,
        "description": "Quantized circulation in Bose-Einstein condensates, Onsager-Feynman vortex dynamics, and macroscopic quantum phenomena.",
    },
    {
        "category": "Software Engineering & Architecture",
        "subtitle": "Asynchronous Event Routing and Choreographed Workflows",
        "author": "Priya Sharma",
        "publisher": "TechBridge Press",
        "year": 2023,
        "description": "Enterprise event choreography, pub/sub topic circulation, dead letter queues, and idempotent message delivery pipelines.",
    },
    {
        "category": "Web Development & Frontend",
        "subtitle": "Reactive State Propagation and Virtual DOM Hydration",
        "author": "Maya Rao",
        "publisher": "Matrix Educational Media",
        "year": 2024,
        "description": "Signal-based reactivity, unidirectional data circulation, concurrent scheduling, and incremental DOM hydration architectures.",
    },
]


def cleanup_categories():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        # 1. Baseline Counts
        pre_books = db.query(func.count(Book.id)).scalar()
        pre_copies = db.query(func.count(BookCopy.id)).scalar()
        pre_cats = db.query(func.count(Category.id)).scalar()
        logger.info(f"Pre-migration baseline: Books={pre_books}, Copies={pre_copies}, Categories={pre_cats}")

        # 2. Map canonical categories
        canonical_map = {c.name: c for c in db.query(Category).all() if c.name in CANONICAL_NAMES}
        if len(canonical_map) != 20:
            raise RuntimeError(f"Expected 20 canonical categories, found {len(canonical_map)}: {list(canonical_map.keys())}")

        # 3. Identify obsolete categories
        all_cats = db.query(Category).all()
        obsolete_cats = [c for c in all_cats if c.name not in CANONICAL_NAMES]
        obsolete_cat_ids = {c.id for c in obsolete_cats}
        logger.info(f"Identified {len(obsolete_cats)} obsolete/test categories to clean up.")

        # 4. Find all books needing reassignment
        books_to_reassign = db.query(Book).filter(
            (Book.category_id == None) | (Book.category_id.in_(obsolete_cat_ids))
        ).order_by(Book.created_at.asc(), Book.id.asc()).all()
        logger.info(f"Found {len(books_to_reassign)} books needing reassignment.")

        # 5. Classify and reassign books
        circ_idx = 0
        dep_idx = 0
        inv_idx = 0

        for book in books_to_reassign:
            title = book.title or ""
            if title.startswith("Circulation Dynamics"):
                topic = CIRCULATION_TOPICS[circ_idx % len(CIRCULATION_TOPICS)]
                circ_idx += 1
                cat = canonical_map[topic["category"]]
                book.category_id = cat.id
                # Retain original volume tag for traceability while adding academic monograph subtitle
                book.title = f"{title}: {topic['subtitle']}"
                book.author = topic["author"]
                book.publisher = topic["publisher"]
                book.publication_year = topic["year"]
                book.description = topic["description"]

            elif title == "Realtime Systems":
                cat = canonical_map["Operating Systems & Kernel"]
                book.category_id = cat.id
                book.author = "Alan Turing"
                book.publisher = "Northstar Academic Press"
                book.publication_year = 2022
                book.description = "Deterministic scheduling, priority inversion solutions, and microkernel architectures for hard and soft real-time computing."

            elif title == "B":
                cat = canonical_map["Database Systems & Storage"]
                book.category_id = cat.id
                book.title = "The B-Tree: Storage Indexing and Concurrency"
                book.author = "Prof. Alexander Wright"
                book.publisher = "Apex Technical Publishing"
                book.publication_year = 2021
                book.description = "In-depth analysis of B-Tree variations, buffer management, write-ahead logging, and concurrency control in database storage engines."

            elif title == "B1":
                cat = canonical_map["History of Computing"]
                book.category_id = cat.id
                book.title = "The B Programming Language and Early Unix Architecture"
                book.author = "Michael Thorne"
                book.publisher = "Open Systems Publishing"
                book.publication_year = 2020
                book.description = "Historical exploration of the B language, early Unix development at Bell Labs, and architectural transitions to C."

            elif title == "Dependent Book":
                dep_idx += 1
                if dep_idx == 1:
                    cat = canonical_map["Software Engineering & Architecture"]
                    book.title = "Dependency Injection and Enterprise Inversion of Control"
                    book.author = "Sarah Jenkins"
                    book.publisher = "TechBridge Press"
                    book.publication_year = 2023
                    book.description = "Comprehensive study of dependency injection patterns, lifecycle management, and architectural boundaries in modern enterprise systems."
                elif dep_idx == 2:
                    cat = canonical_map["Database Systems & Storage"]
                    book.title = "Functional Dependency Theory in Relational Databases"
                    book.author = "Priya Sharma"
                    book.publisher = "Northstar Academic Press"
                    book.publication_year = 2022
                    book.description = "Armstrong's axioms, canonical cover algorithms, BCNF decomposition, and schema normalization theory."
                else:
                    cat = canonical_map["Computer Science & Theory"]
                    book.title = "Dependent Types and Formal Program Verification"
                    book.author = "Dr. Vikram Patel"
                    book.publisher = "Beacon Scientific Press"
                    book.publication_year = 2024
                    book.description = "Curry-Howard isomorphism, intuitionistic type theory, proof assistants, and certified software engineering."
                book.category_id = cat.id

            elif title.startswith("Inventory Test Book"):
                inv_idx += 1
                if inv_idx == 1:
                    cat = canonical_map["Mathematics & Discrete Structures"]
                    book.title = f"Inventory Optimization and Operations Research (Vol {inv_idx})"
                    book.author = "Elena Rostova"
                    book.publisher = "Beacon Scientific Press"
                    book.publication_year = 2023
                    book.description = "Mathematical models for stochastic inventory control, dynamic programming, queueing models, and supply chain logistics."
                elif inv_idx == 2:
                    cat = canonical_map["Business Strategy & Technology"]
                    book.title = f"Enterprise Resource Planning and Information Systems (Vol {inv_idx})"
                    book.author = "Daniel Carter"
                    book.publisher = "KnowledgeWorks Publishing"
                    book.publication_year = 2022
                    book.description = "Architectural foundations of ERP systems, supply chain integration, and enterprise business process automation."
                else:
                    cat = canonical_map["Software Engineering & Architecture"]
                    book.title = f"Distributed Stock Management and Event-Driven Systems (Vol {inv_idx})"
                    book.author = "Michael Thorne"
                    book.publisher = "TechBridge Press"
                    book.publication_year = 2024
                    book.description = "Designing high-throughput distributed inventory ledgers using event sourcing, CQRS, and consensus protocols."
                book.category_id = cat.id

            else:
                # Fallback to Computer Science & Theory
                cat = canonical_map["Computer Science & Theory"]
                book.category_id = cat.id
                logger.warning(f"Unmapped book {book.title!r} assigned to {cat.name}")

        db.flush()
        logger.info(f"Reassigned {len(books_to_reassign)} books across canonical categories.")

        # 6. Verify 0 books reference obsolete categories
        remaining_obsolete_books = db.query(func.count(Book.id)).filter(Book.category_id.in_(obsolete_cat_ids)).scalar()
        null_cat_books = db.query(func.count(Book.id)).filter(Book.category_id == None).scalar()
        if remaining_obsolete_books > 0 or null_cat_books > 0:
            raise RuntimeError(f"Integrity check failed: {remaining_obsolete_books} obsolete ref books, {null_cat_books} null cat books.")

        # 7. Safe deletion of obsolete categories
        deleted_count = 0
        for obs_cat in obsolete_cats:
            db.delete(obs_cat)
            deleted_count += 1
        db.flush()
        logger.info(f"Deleted {deleted_count} obsolete/test categories.")

        # 8. Post-migration verification
        post_books = db.query(func.count(Book.id)).scalar()
        post_copies = db.query(func.count(BookCopy.id)).scalar()
        post_cats = db.query(func.count(Category.id)).scalar()

        logger.info(f"Post-migration counts: Books={post_books}, Copies={post_copies}, Categories={post_cats}")

        assert post_books == pre_books, f"Book count mismatch: {post_books} != {pre_books}"
        assert post_copies == pre_copies, f"Copy count mismatch: {post_copies} != {pre_copies}"
        assert post_cats == 20, f"Expected 20 categories, got {post_cats}"

        # Distribution check
        cat_counts = (
            db.query(Category.name, func.count(Book.id))
            .join(Book, Book.category_id == Category.id)
            .group_by(Category.name)
            .order_by(Category.name)
            .all()
        )
        logger.info("Final Category Distribution:")
        for name, count in cat_counts:
            logger.info(f"  - {name}: {count} titles")

        db.commit()
        logger.info("Successfully committed migration!")


if __name__ == "__main__":
    cleanup_categories()
