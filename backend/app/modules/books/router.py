"""
Library Catalog Management HTTP Router.

Provides endpoints for:
  - Categories: /categories
  - Books: /books
  - Physical Copies: /books/{book_id}/copies and /copies/{copy_id}

AUTHORIZATION:
  - Read operations require `book:view` (AppPermission.BOOK_VIEW)
  - Create operations require `book:create` (AppPermission.BOOK_CREATE)
  - Update operations require `book:update` (AppPermission.BOOK_UPDATE)
  - Delete operations require `book:delete` (AppPermission.BOOK_DELETE)
"""

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.book_copy import CopyStatus
from app.models.user import User
from app.modules.books.schemas import (
    BookCopyCreate,
    BookCopyListResponse,
    BookCopyOut,
    BookCopyUpdate,
    BookCreate,
    BookListResponse,
    BookOut,
    BookUpdate,
    CategoryCreate,
    CategoryListResponse,
    CategoryOut,
    CategoryUpdate,
)
from app.modules.books.service import book_service, category_service, copy_service
from app.modules.permissions.constants import AppPermission
from app.modules.permissions.dependencies import require_permission

# Router definitions
category_router = APIRouter(prefix="/categories", tags=["categories"])
book_router = APIRouter(prefix="/books", tags=["books"])
copy_router = APIRouter(tags=["book-copies"])


def _extract_request_meta(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract IP and User-Agent from request state or headers."""
    ip = getattr(request.state, "client_ip", None) or (
        request.client.host if request.client else None
    )
    ua = getattr(request.state, "user_agent", None) or request.headers.get("user-agent")
    return ip, ua


# ===========================================================================
# CATEGORY ENDPOINTS
# ===========================================================================


@category_router.get(
    "",
    response_model=CategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List categories",
    description="Lists all book categories with optional search filtering and pagination. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def list_categories(
    search: Optional[str] = Query(None, description="Filter categories by name substring"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> CategoryListResponse:
    items, total, pages = category_service.list_categories(
        db=db,
        search=search,
        page=page,
        page_size=page_size,
    )
    return CategoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@category_router.get(
    "/{category_id}",
    response_model=CategoryOut,
    status_code=status.HTTP_200_OK,
    summary="Get category by ID",
    description="Retrieves a specific book category by its UUID. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> CategoryOut:
    return category_service.get_category_by_id(db=db, category_id=category_id)


@category_router.post(
    "",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Creates a new book category with unique name. Requires 'book:create'.",
)
def create_category(
    data: CategoryCreate,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_CREATE.value)),
    db: Session = Depends(get_db),
) -> CategoryOut:
    ip, ua = _extract_request_meta(request)
    return category_service.create_category(
        db=db,
        data=data,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@category_router.put(
    "/{category_id}",
    response_model=CategoryOut,
    status_code=status.HTTP_200_OK,
    summary="Update category",
    description="Updates existing category metadata. Requires 'book:update'.",
)
def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_UPDATE.value)),
    db: Session = Depends(get_db),
) -> CategoryOut:
    ip, ua = _extract_request_meta(request)
    return category_service.update_category(
        db=db,
        category_id=category_id,
        data=data,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@category_router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete category",
    description="Deletes a category if no books are associated with it. Requires 'book:delete'.",
)
def delete_category(
    category_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_DELETE.value)),
    db: Session = Depends(get_db),
) -> dict:
    ip, ua = _extract_request_meta(request)
    category_service.delete_category(
        db=db,
        category_id=category_id,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )
    return {"message": f"Category '{category_id}' deleted successfully"}


# ===========================================================================
# BOOK ENDPOINTS
# ===========================================================================


@book_router.get(
    "",
    response_model=BookListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and search books",
    description=(
        "Retrieves a paginated list of books with support for keyword search (title, author, ISBN, publisher), "
        "category filtering, and author filtering. Requires 'book:view'."
    ),
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def list_books(
    search: Optional[str] = Query(None, description="Search query matching title, author, ISBN, or publisher"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by Category UUID"),
    author: Optional[str] = Query(None, description="Filter by author name substring"),
    publication_year: Optional[int] = Query(None, description="Filter by 4-digit publication year"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> BookListResponse:
    items, total, pages = book_service.list_books(
        db=db,
        search=search,
        category_id=category_id,
        author=author,
        publication_year=publication_year,
        page=page,
        page_size=page_size,
    )
    return BookListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@book_router.get(
    "/{book_id}",
    response_model=BookOut,
    status_code=status.HTTP_200_OK,
    summary="Get book details by ID",
    description="Retrieves a single book title by its UUID, including copy inventory statistics. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def get_book(
    book_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> BookOut:
    return book_service.get_book_by_id(db=db, book_id=book_id)


@book_router.post(
    "",
    response_model=BookOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create book title",
    description="Adds a new book title to the catalogue. Enforces ISBN uniqueness. Requires 'book:create'.",
)
def create_book(
    data: BookCreate,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_CREATE.value)),
    db: Session = Depends(get_db),
) -> BookOut:
    ip, ua = _extract_request_meta(request)
    return book_service.create_book(
        db=db,
        data=data,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@book_router.put(
    "/{book_id}",
    response_model=BookOut,
    status_code=status.HTTP_200_OK,
    summary="Update book metadata",
    description="Updates existing book title metadata and category reference. Requires 'book:update'.",
)
def update_book(
    book_id: uuid.UUID,
    data: BookUpdate,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_UPDATE.value)),
    db: Session = Depends(get_db),
) -> BookOut:
    ip, ua = _extract_request_meta(request)
    return book_service.update_book(
        db=db,
        book_id=book_id,
        data=data,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@book_router.delete(
    "/{book_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete book",
    description="Deletes a book title from the catalogue if no physical copies exist. Requires 'book:delete'.",
)
def delete_book(
    book_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_DELETE.value)),
    db: Session = Depends(get_db),
) -> dict:
    ip, ua = _extract_request_meta(request)
    book_service.delete_book(
        db=db,
        book_id=book_id,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )
    return {"message": f"Book '{book_id}' deleted successfully"}


# ===========================================================================
# BOOK COPIES ENDPOINTS
# ===========================================================================


@book_router.get(
    "/{book_id}/copies",
    response_model=BookCopyListResponse,
    status_code=status.HTTP_200_OK,
    summary="List copies of a book",
    description="Lists all physical inventory copies associated with a specific book title. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def list_book_copies(
    book_id: uuid.UUID,
    status: Optional[CopyStatus] = Query(None, description="Filter copies by availability status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> BookCopyListResponse:
    items, total, pages = copy_service.list_copies_for_book(
        db=db,
        book_id=book_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return BookCopyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@book_router.post(
    "/{book_id}/copies",
    response_model=BookCopyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create book copy",
    description="Registers a new physical copy for a book title with unique barcode/identifier. Requires 'book:create'.",
)
def create_book_copy(
    book_id: uuid.UUID,
    data: BookCopyCreate,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_CREATE.value)),
    db: Session = Depends(get_db),
) -> BookCopyOut:
    ip, ua = _extract_request_meta(request)
    return copy_service.create_copy(
        db=db,
        book_id=book_id,
        data=data,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@copy_router.get(
    "/copies/{copy_id}",
    response_model=BookCopyOut,
    status_code=status.HTTP_200_OK,
    summary="Get copy by ID",
    description="Retrieves a specific physical copy record by its UUID. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def get_copy(
    copy_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> BookCopyOut:
    return copy_service.get_copy_by_id(db=db, copy_id=copy_id)


@copy_router.put(
    "/copies/{copy_id}",
    response_model=BookCopyOut,
    status_code=status.HTTP_200_OK,
    summary="Update copy details",
    description="Updates physical copy location, barcode, or status. Requires 'book:update'.",
)
def update_copy(
    copy_id: uuid.UUID,
    data: BookCopyUpdate,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_UPDATE.value)),
    db: Session = Depends(get_db),
) -> BookCopyOut:
    ip, ua = _extract_request_meta(request)
    return copy_service.update_copy(
        db=db,
        copy_id=copy_id,
        data=data,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@copy_router.delete(
    "/copies/{copy_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete copy",
    description="Removes a physical copy from inventory if not actively borrowed. Requires 'book:delete'.",
)
def delete_copy(
    copy_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_DELETE.value)),
    db: Session = Depends(get_db),
) -> dict:
    ip, ua = _extract_request_meta(request)
    copy_service.delete_copy(
        db=db,
        copy_id=copy_id,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )
    return {"message": f"Book copy '{copy_id}' deleted successfully"}
