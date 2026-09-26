"""
Catalog Service Layer.

Provides business logic and data access for:
  - CategoryService
  - BookService
  - BookCopyService

ENFORCES:
  - Input validation and referential integrity
  - Unique constraints (Category name, Book ISBN, BookCopy copy_identifier)
  - Protected deletion policies (cannot delete category with books, cannot delete book with copies)
  - Security and operational audit logging via AuditService
  - Transaction safety
"""

from math import ceil
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.audit_log import AuditAction, AuditStatus
from app.models.book import Book
from app.models.book_copy import BookCopy, CopyStatus
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.category import Category
from app.modules.audit.service import audit_service
from app.modules.books.schemas import (
    BookCopyCreate,
    BookCopyOut,
    BookCopyUpdate,
    BookCreate,
    BookOut,
    BookUpdate,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
)

logger = get_logger(__name__)


class CategoryService:
    """Business service for book categories / genres."""

    @staticmethod
    def list_categories(
        db: Session,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[CategoryOut], int, int]:
        """
        List categories with optional search filtering and pagination.
        Returns: (items, total_count, total_pages)
        """
        query = db.query(Category)

        if search and search.strip():
            clean_search = f"%{search.strip()}%"
            query = query.filter(Category.name.ilike(clean_search))

        total = query.count()
        pages = ceil(total / page_size) if total > 0 else 1
        offset = max(0, (page - 1) * page_size)

        categories = (
            query.order_by(Category.name.asc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # Compute book count for each category
        category_ids = [c.id for c in categories]
        counts_map = {}
        if category_ids:
            count_rows = (
                db.query(Book.category_id, func.count(Book.id))
                .filter(Book.category_id.in_(category_ids))
                .group_by(Book.category_id)
                .all()
            )
            counts_map = {row[0]: row[1] for row in count_rows}

        results = [
            CategoryOut(
                id=c.id,
                name=c.name,
                description=c.description,
                book_count=counts_map.get(c.id, 0),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in categories
        ]

        return results, total, pages

    @staticmethod
    def get_category_by_id(db: Session, category_id: uuid.UUID) -> CategoryOut:
        """
        Retrieve a single Category by UUID.
        Raises NotFoundError if not found.
        """
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise NotFoundError(f"Category with ID '{category_id}' not found.")

        book_count = db.query(Book).filter(Book.category_id == category_id).count()

        return CategoryOut(
            id=category.id,
            name=category.name,
            description=category.description,
            book_count=book_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )

    @staticmethod
    def create_category(
        db: Session,
        data: CategoryCreate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CategoryOut:
        """
        Create a new category. Enforces unique category name.
        """
        clean_name = data.name.strip()
        existing = (
            db.query(Category)
            .filter(func.lower(Category.name) == clean_name.lower())
            .first()
        )
        if existing:
            raise ConflictError(f"Category with name '{clean_name}' already exists.")

        category = Category(
            name=clean_name,
            description=data.description.strip() if data.description else None,
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_CREATED,
            user_id=user_id,
            resource_type="Category",
            resource_id=str(category.id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.CATEGORY_CREATED,
                resource_type="Category",
                resource_id=str(category.id),
                actor_user_id=user_id,
                data={"name": category.name},
            )
        except Exception:
            pass

        return CategoryOut(
            id=category.id,
            name=category.name,
            description=category.description,
            book_count=0,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )

    @staticmethod
    def update_category(
        db: Session,
        category_id: uuid.UUID,
        data: CategoryUpdate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CategoryOut:
        """
        Update category metadata. Enforces unique name if modified.
        """
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise NotFoundError(f"Category with ID '{category_id}' not found.")

        if data.name is not None:
            clean_name = data.name.strip()
            if clean_name.lower() != category.name.lower():
                existing = (
                    db.query(Category)
                    .filter(
                        func.lower(Category.name) == clean_name.lower(),
                        Category.id != category_id,
                    )
                    .first()
                )
                if existing:
                    raise ConflictError(
                        f"Category with name '{clean_name}' already exists."
                    )
            category.name = clean_name

        if data.description is not None:
            category.description = (
                data.description.strip() if data.description else None
            )

        db.commit()
        db.refresh(category)

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_UPDATED,
            user_id=user_id,
            resource_type="Category",
            resource_id=str(category.id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.CATEGORY_UPDATED,
                resource_type="Category",
                resource_id=str(category.id),
                actor_user_id=user_id,
                data={"name": category.name},
            )
        except Exception:
            pass

        book_count = db.query(Book).filter(Book.category_id == category.id).count()

        return CategoryOut(
            id=category.id,
            name=category.name,
            description=category.description,
            book_count=book_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )

    @staticmethod
    def delete_category(
        db: Session,
        category_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Delete a Category.
        Rejects deletion if books are assigned to this category.
        """
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise NotFoundError(f"Category with ID '{category_id}' not found.")

        book_count = db.query(Book).filter(Book.category_id == category_id).count()
        if book_count > 0:
            raise ConflictError(
                f"Cannot delete category '{category.name}' because it contains {book_count} book(s). "
                "Please reassign or remove the books first."
            )

        db.delete(category)
        db.commit()

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_DELETED,
            user_id=user_id,
            resource_type="Category",
            resource_id=str(category_id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.CATEGORY_DELETED,
                resource_type="Category",
                resource_id=str(category_id),
                actor_user_id=user_id,
            )
        except Exception:
            pass

        return True


class BookService:
    """Business service for Book catalogue management."""

    @staticmethod
    def list_books(
        db: Session,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        author: Optional[str] = None,
        publication_year: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[BookOut], int, int]:
        """
        Retrieve paginated book catalog with search, category filtering, and copy counts.
        Returns: (items, total_count, total_pages)
        """
        query = db.query(Book).options(
            joinedload(Book.category),
            selectinload(Book.copies),
        )

        if category_id:
            query = query.filter(Book.category_id == category_id)

        if author and author.strip():
            query = query.filter(Book.author.ilike(f"%{author.strip()}%"))

        if publication_year:
            query = query.filter(Book.publication_year == publication_year)

        if search and search.strip():
            clean_search = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Book.title.ilike(clean_search),
                    Book.author.ilike(clean_search),
                    Book.isbn.ilike(clean_search),
                    Book.publisher.ilike(clean_search),
                )
            )

        total = query.count()
        pages = ceil(total / page_size) if total > 0 else 1
        offset = max(0, (page - 1) * page_size)

        books = (
            query.order_by(Book.title.asc(), Book.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        results = [
            BookOut(
                id=b.id,
                title=b.title,
                author=b.author,
                isbn=b.isbn,
                publisher=b.publisher,
                publication_year=b.publication_year,
                description=b.description,
                category_id=b.category_id,
                category_name=b.category.name if b.category else None,
                total_copies=len(b.copies),
                available_copies=sum(
                    1 for c in b.copies if c.status == CopyStatus.AVAILABLE
                ),
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
            for b in books
        ]

        return results, total, pages

    @staticmethod
    def get_book_by_id(db: Session, book_id: uuid.UUID) -> BookOut:
        """
        Retrieve a single Book title with category and copy counts.
        Raises NotFoundError if not found.
        """
        book = (
            db.query(Book)
            .options(
                joinedload(Book.category),
                selectinload(Book.copies),
            )
            .filter(Book.id == book_id)
            .first()
        )
        if not book:
            raise NotFoundError(f"Book with ID '{book_id}' not found.")

        return BookOut(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            publisher=book.publisher,
            publication_year=book.publication_year,
            description=book.description,
            category_id=book.category_id,
            category_name=book.category.name if book.category else None,
            total_copies=len(book.copies),
            available_copies=sum(
                1 for c in book.copies if c.status == CopyStatus.AVAILABLE
            ),
            created_at=book.created_at,
            updated_at=book.updated_at,
        )

    @staticmethod
    def create_book(
        db: Session,
        data: BookCreate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> BookOut:
        """
        Create a new Book title.
        Validates category reference and unique ISBN constraint.
        """
        category_name = None
        if data.category_id:
            category = (
                db.query(Category).filter(Category.id == data.category_id).first()
            )
            if not category:
                raise NotFoundError(
                    f"Category with ID '{data.category_id}' does not exist."
                )
            category_name = category.name

        clean_isbn = data.isbn.strip() if data.isbn else None
        if clean_isbn:
            existing_isbn = (
                db.query(Book).filter(Book.isbn == clean_isbn).first()
            )
            if existing_isbn:
                raise ConflictError(
                    f"Book with ISBN '{clean_isbn}' already exists (Title: '{existing_isbn.title}')."
                )

        book = Book(
            title=data.title.strip(),
            author=data.author.strip(),
            isbn=clean_isbn,
            publisher=data.publisher.strip() if data.publisher else None,
            publication_year=data.publication_year,
            description=data.description.strip() if data.description else None,
            category_id=data.category_id,
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_CREATED,
            user_id=user_id,
            resource_type="Book",
            resource_id=str(book.id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.BOOK_CREATED,
                resource_type="Book",
                resource_id=str(book.id),
                actor_user_id=user_id,
                data={"title": book.title, "isbn": book.isbn},
            )
        except Exception:
            pass

        return BookOut(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            publisher=book.publisher,
            publication_year=book.publication_year,
            description=book.description,
            category_id=book.category_id,
            category_name=category_name,
            total_copies=0,
            available_copies=0,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )

    @staticmethod
    def update_book(
        db: Session,
        book_id: uuid.UUID,
        data: BookUpdate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> BookOut:
        """
        Update Book metadata.
        Validates category reference and unique ISBN if updated.
        """
        book = (
            db.query(Book)
            .options(
                joinedload(Book.category),
                selectinload(Book.copies),
            )
            .filter(Book.id == book_id)
            .first()
        )
        if not book:
            raise NotFoundError(f"Book with ID '{book_id}' not found.")

        if data.category_id is not None:
            if data.category_id != book.category_id:
                category = (
                    db.query(Category).filter(Category.id == data.category_id).first()
                )
                if not category:
                    raise NotFoundError(
                        f"Category with ID '{data.category_id}' does not exist."
                    )
            book.category_id = data.category_id

        if data.isbn is not None:
            clean_isbn = data.isbn.strip() if data.isbn else None
            if clean_isbn and clean_isbn != book.isbn:
                existing_isbn = (
                    db.query(Book)
                    .filter(Book.isbn == clean_isbn, Book.id != book_id)
                    .first()
                )
                if existing_isbn:
                    raise ConflictError(
                        f"Book with ISBN '{clean_isbn}' already exists (Title: '{existing_isbn.title}')."
                    )
            book.isbn = clean_isbn

        if data.title is not None:
            book.title = data.title.strip()
        if data.author is not None:
            book.author = data.author.strip()
        if data.publisher is not None:
            book.publisher = data.publisher.strip() if data.publisher else None
        if data.publication_year is not None:
            book.publication_year = data.publication_year
        if data.description is not None:
            book.description = data.description.strip() if data.description else None

        db.commit()
        db.refresh(book)

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_UPDATED,
            user_id=user_id,
            resource_type="Book",
            resource_id=str(book.id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.BOOK_UPDATED,
                resource_type="Book",
                resource_id=str(book.id),
                actor_user_id=user_id,
                data={"title": book.title, "isbn": book.isbn},
            )
        except Exception:
            pass

        return BookOut(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            publisher=book.publisher,
            publication_year=book.publication_year,
            description=book.description,
            category_id=book.category_id,
            category_name=book.category.name if book.category else None,
            total_copies=len(book.copies),
            available_copies=sum(
                1 for c in book.copies if c.status == CopyStatus.AVAILABLE
            ),
            created_at=book.created_at,
            updated_at=book.updated_at,
        )

    @staticmethod
    def delete_book(
        db: Session,
        book_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Delete a Book title.
        Rejects deletion if physical copies exist in inventory.
        """
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise NotFoundError(f"Book with ID '{book_id}' not found.")

        copies_count = (
            db.query(BookCopy).filter(BookCopy.book_id == book_id).count()
        )
        if copies_count > 0:
            raise ConflictError(
                f"Cannot delete book '{book.title}' because it has {copies_count} physical "
                "copy/copies in inventory. Please delete all physical copies first."
            )

        db.delete(book)
        db.commit()

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_DELETED,
            user_id=user_id,
            resource_type="Book",
            resource_id=str(book_id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.BOOK_DELETED,
                resource_type="Book",
                resource_id=str(book_id),
                actor_user_id=user_id,
            )
        except Exception:
            pass

        return True


class BookCopyService:
    """Business service for physical BookCopy inventory management."""

    @staticmethod
    def list_copies_for_book(
        db: Session,
        book_id: uuid.UUID,
        status: Optional[CopyStatus] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[BookCopyOut], int, int]:
        """
        List all physical copies for a specific book title.
        Returns: (items, total_count, total_pages)
        """
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise NotFoundError(f"Book with ID '{book_id}' not found.")

        query = db.query(BookCopy).filter(BookCopy.book_id == book_id)
        if status:
            query = query.filter(BookCopy.status == status)

        total = query.count()
        pages = ceil(total / page_size) if total > 0 else 1
        offset = max(0, (page - 1) * page_size)

        copies = (
            query.order_by(BookCopy.copy_identifier.asc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        results = [
            BookCopyOut(
                id=c.id,
                book_id=c.book_id,
                copy_identifier=c.copy_identifier,
                status=c.status,
                shelf_location=c.shelf_location,
                book_title=book.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in copies
        ]

        return results, total, pages

    @staticmethod
    def get_copy_by_id(db: Session, copy_id: uuid.UUID) -> BookCopyOut:
        """
        Retrieve a single BookCopy by UUID.
        Raises NotFoundError if not found.
        """
        copy = (
            db.query(BookCopy)
            .options(joinedload(BookCopy.book))
            .filter(BookCopy.id == copy_id)
            .first()
        )
        if not copy:
            raise NotFoundError(f"Book copy with ID '{copy_id}' not found.")

        return BookCopyOut(
            id=copy.id,
            book_id=copy.book_id,
            copy_identifier=copy.copy_identifier,
            status=copy.status,
            shelf_location=copy.shelf_location,
            book_title=copy.book.title if copy.book else None,
            created_at=copy.created_at,
            updated_at=copy.updated_at,
        )

    @staticmethod
    def create_copy(
        db: Session,
        book_id: uuid.UUID,
        data: BookCopyCreate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> BookCopyOut:
        """
        Create a new physical copy for a book title.
        Enforces unique copy_identifier constraint.
        """
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise NotFoundError(f"Book with ID '{book_id}' not found.")

        clean_identifier = data.copy_identifier.strip()
        existing = (
            db.query(BookCopy)
            .filter(BookCopy.copy_identifier == clean_identifier)
            .first()
        )
        if existing:
            raise ConflictError(
                f"Book copy with identifier '{clean_identifier}' already exists."
            )

        copy = BookCopy(
            book_id=book_id,
            copy_identifier=clean_identifier,
            shelf_location=data.shelf_location.strip()
            if data.shelf_location
            else None,
            status=data.status or CopyStatus.AVAILABLE,
        )
        db.add(copy)
        db.commit()
        db.refresh(copy)

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_CREATED,
            user_id=user_id,
            resource_type="BookCopy",
            resource_id=str(copy.id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.COPY_CREATED,
                resource_type="BookCopy",
                resource_id=str(copy.id),
                actor_user_id=user_id,
                data={"book_id": str(copy.book_id), "copy_identifier": copy.copy_identifier},
            )
        except Exception:
            pass

        return BookCopyOut(
            id=copy.id,
            book_id=copy.book_id,
            copy_identifier=copy.copy_identifier,
            status=copy.status,
            shelf_location=copy.shelf_location,
            book_title=book.title,
            created_at=copy.created_at,
            updated_at=copy.updated_at,
        )

    @staticmethod
    def update_copy(
        db: Session,
        copy_id: uuid.UUID,
        data: BookCopyUpdate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> BookCopyOut:
        """
        Update physical copy details. Enforces unique copy_identifier if changed.
        """
        copy = (
            db.query(BookCopy)
            .options(joinedload(BookCopy.book))
            .filter(BookCopy.id == copy_id)
            .first()
        )
        if not copy:
            raise NotFoundError(f"Book copy with ID '{copy_id}' not found.")

        if data.copy_identifier is not None:
            clean_identifier = data.copy_identifier.strip()
            if clean_identifier != copy.copy_identifier:
                existing = (
                    db.query(BookCopy)
                    .filter(
                        BookCopy.copy_identifier == clean_identifier,
                        BookCopy.id != copy_id,
                    )
                    .first()
                )
                if existing:
                    raise ConflictError(
                        f"Book copy with identifier '{clean_identifier}' already exists."
                    )
            copy.copy_identifier = clean_identifier

        if data.shelf_location is not None:
            copy.shelf_location = (
                data.shelf_location.strip() if data.shelf_location else None
            )

        if data.status is not None:
            copy.status = data.status

        db.commit()
        db.refresh(copy)

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_UPDATED,
            user_id=user_id,
            resource_type="BookCopy",
            resource_id=str(copy.id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.COPY_UPDATED,
                resource_type="BookCopy",
                resource_id=str(copy.id),
                actor_user_id=user_id,
                data={
                    "book_id": str(copy.book_id),
                    "copy_identifier": copy.copy_identifier,
                    "status": copy.status.value,
                },
            )
        except Exception:
            pass

        return BookCopyOut(
            id=copy.id,
            book_id=copy.book_id,
            copy_identifier=copy.copy_identifier,
            status=copy.status,
            shelf_location=copy.shelf_location,
            book_title=copy.book.title if copy.book else None,
            created_at=copy.created_at,
            updated_at=copy.updated_at,
        )

    @staticmethod
    def delete_copy(
        db: Session,
        copy_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Delete a physical copy from inventory.
        Prevents deletion if copy is currently active in a borrow transaction.
        """
        copy = db.query(BookCopy).filter(BookCopy.id == copy_id).first()
        if not copy:
            raise NotFoundError(f"Book copy with ID '{copy_id}' not found.")

        # Check if copy is currently actively borrowed
        active_borrow = (
            db.query(BorrowRecord)
            .filter(
                BorrowRecord.book_copy_id == copy_id,
                BorrowRecord.status == BorrowStatus.ACTIVE,
            )
            .first()
        )
        if active_borrow:
            raise ConflictError(
                f"Cannot delete copy '{copy.copy_identifier}' because it is currently borrowed by a user."
            )

        db.delete(copy)
        db.commit()

        audit_service.log(
            db=db,
            action=AuditAction.BOOK_DELETED,
            user_id=user_id,
            resource_type="BookCopy",
            resource_id=str(copy_id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.COPY_DELETED,
                resource_type="BookCopy",
                resource_id=str(copy_id),
                actor_user_id=user_id,
            )
        except Exception:
            pass

        return True


category_service = CategoryService()
book_service = BookService()
copy_service = BookCopyService()
