# PustakHub — Demo Data & Seed Subsystem

> **Phase 11 — Safe, Deterministic Demo Data Seeding**  
> Last updated: 2026-09-24

---

## 1. Executive Overview

PustakHub includes a dedicated, production-safe, deterministic demo data seeding subsystem located in `backend/scripts/seed_demo.py`.

The seed subsystem exists to populate a realistic, domain-rich dataset for:
- Developer local onboarding and UI testing
- Interactive demonstrations and presentations
- Realistic dashboard search, filtering, and pagination screenshots
- Circulation workflows and overdue fine validation
- RBAC role testing across all four primary platform roles

---

## 2. Dataset Composition

The seed system deterministically generates:

| Entity | Quantity | Characteristics |
| :--- | :---: | :--- |
| **Categories** | 20 | Diverse technical and academic genres (e.g., *Computer Science*, *Distributed Systems*, *Cybersecurity*, *AI*). |
| **Books** | 500 | High-quality synthetic titles, realistic author combinations, diverse publishers, and mathematically valid ISBN-13 identifiers. |
| **Book Copies** | 1,178 | Physical inventory copies with unique barcodes (`PUSTAK-0001-01`), shelf bay locations, and status distribution. |
| **Demo Users** | 9 | Dedicated demo accounts for all 4 roles (`ADMIN`, `LIBRARIAN`, `STUDENT`, `GUEST`) plus 5 student patrons. |
| **Borrow Records** | 100 | Realistic mix: 25 active on-time loans, 15 active overdue loans, 45 returned on-time, 15 returned late. |
| **Overdue Fines** | 15 | Exactly calculated at `$2.00/day` overdue penalties linked 1:1 with late return records (10 PENDING, 5 PAID). |

---

## 3. Demo User Credentials (LOCAL DEVELOPMENT ONLY)

> [!WARNING]
> The credentials below are strictly for **local development and demonstration purposes**. Never use these passwords in a production deployment.

| Role | Email | Default Development Password | Environment Variable Override |
| :--- | :--- | :--- | :--- |
| **ADMIN** | `admin.demo@pustakhub.com` | `PustakHubDemo!2026#Admin` | `DEMO_ADMIN_PASSWORD` |
| **LIBRARIAN** | `librarian.demo@pustakhub.com` | `PustakHubDemo!2026#Library` | `DEMO_LIBRARIAN_PASSWORD` |
| **STUDENT** | `student.demo@pustakhub.com` | `PustakHubDemo!2026#Student` | `DEMO_STUDENT_PASSWORD` |
| **GUEST** | `guest.demo@pustakhub.com` | `PustakHubDemo!2026#Guest` | `DEMO_GUEST_PASSWORD` |

### Additional Student Patrons
- `student.aarav@pustakhub.com` / `PustakHubDemo!2026#Student`
- `student.diya@pustakhub.com` / `PustakHubDemo!2026#Student`
- `student.neha@pustakhub.com` / `PustakHubDemo!2026#Student`
- `student.vikram@pustakhub.com` / `PustakHubDemo!2026#Student`
- `student.ananya@pustakhub.com` / `PustakHubDemo!2026#Student`

All passwords are processed using production-standard **Argon2id** memory-hard hashing via `argon2-cffi`. No plaintext passwords exist in the database.

---

## 4. CLI Usage

All seeding commands are executed from the `backend/` directory with the virtual environment activated:

### 4.1 Seed the Database
```bash
cd backend
python scripts/seed_demo.py
```

To specify a custom deterministic random seed:
```bash
python scripts/seed_demo.py --seed-number 20260924
```

### 4.2 Reset Demo Data
Safely deletes only demo-tagged records without dropping the database schema or affecting real records:
```bash
python scripts/seed_demo.py --reset-demo
```

### 4.3 CLI Flags Reference
```text
options:
  -h, --help            Show help message and exit
  --reset-demo          Safely remove all seeded demo data (books, copies, demo users, borrows, fines)
  --seed-number SEED    Deterministic integer seed for RNG (default: 20260924)
  --force-production-seed
                        Explicitly allow seeding/reset in ENVIRONMENT=production
```

---

## 5. Security & Safety Invariants

1. **No Startup Execution:** Demo data is **NEVER** seeded automatically upon FastAPI application startup (`app/main.py`). Seeding requires explicit developer invocation via CLI.
2. **Production Safety Guard:** If `ENVIRONMENT=production` in `.env`, `scripts/seed_demo.py` immediately aborts with `[SAFETY ERROR]` unless overridden with `--force-production-seed`.
3. **Idempotency Guarantee:** Running `python scripts/seed_demo.py` multiple times updates existing records without duplicating books, copies, or users.
4. **MFA State:** Demo accounts are created with `is_mfa_enabled = False` to allow immediate login during demonstrations. MFA enrollment can be initiated interactively via `/security/mfa`.
5. **ISBN-13 Correctness:** All ISBNs are generated using the standard EAN-13 check digit modulo 10 formula, ensuring 100% compliance with catalog validators.
6. **Borrowing State Alignment:**
   - Every `BORROWED` book copy is strictly aligned with an active/overdue `BorrowRecord`.
   - Every `AVAILABLE` copy is aligned with returned or un-borrowed states.
   - Fines strictly match the library's `$2.00/day` overdue calculation policy.

---

## 6. Testing

The seed system is verified by a dedicated test suite (`backend/tests/test_phase11_seed.py`):
```bash
cd backend
./venv/bin/pytest -v tests/test_phase11_seed.py
```

Tests verify:
- Determinism across random seed values
- Uniqueness of 500 ISBN-13 strings and copy barcodes
- Production environment rejection
- Argon2id password verification
- Borrowing and copy status synchronization
- Overdue fine mathematical accuracy
- Clean database reset and reseeding
