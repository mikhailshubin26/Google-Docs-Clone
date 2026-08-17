# CRUD-роуты для документов
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response

from typing import Annotated, Literal

from app.api.deps import get_current_user_id
from app.api.v1.schemas.document import DocumentResponse, CreateDocumentRequest, DocumentListResponse, \
    DocumentContentResponse, RenameDocumentRequest
from app.application.services.document_service import DocumentService
from app.application.services.export_service import ExportService, UnsupportedExportFormatError
from app.core.di import get_document_service, get_export_service
from app.domain.exceptions import DocumentNotFoundError, PermissionDeniedError

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
        body: CreateDocumentRequest,
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    document = await document_service.create_document(owner_id=user_id, title=body.title)
    return DocumentResponse.from_entity(document)

@router.get("", response_model=DocumentListResponse)
async def list_my_documents(
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        document_service: Annotated[DocumentService, Depends(get_document_service)],
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentListResponse:
    documents = await document_service.list_my_documents(owner_id=user_id, limit=limit, offset=offset)
    return DocumentListResponse(
        items=[DocumentResponse.from_entity(d) for d in documents],
        limit=limit,
        offset=offset,
    )

@router.get("/{document_id}", response_model=DocumentContentResponse)
async def get_document(
        document_id: UUID,
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentContentResponse:
    try:
        document = await document_service.get_document(document_id=document_id, user_id=user_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return DocumentContentResponse.from_entity(document)

@router.patch("/{document_id}", response_model=DocumentResponse)
async def rename_document(
        document_id: UUID,
        body: RenameDocumentRequest,
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    try:
        document = await document_service.rename_document(
            document_id=document_id, user_id=user_id, new_title=body.title
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return DocumentResponse.from_entity(document)

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
        document_id: UUID,
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> None:
    try:
        document = await document_service.delete_document(document_id=document_id, user_id=user_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

@router.get("/{document_id}/export", response_model=None)
async def export_document(
        document_id: UUID,
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        export_service: Annotated[ExportService, Depends(get_export_service)],
        format: Literal["txt", "docx"] = "txt"
) -> Response:
    try:
        content, content_type, filename = await export_service.export_document(
            document_id=document_id,
            user_id=user_id,
            format_name=format,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except UnsupportedExportFormatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )