import pytest

from app.application.services.export_service import ExportService, UnsupportedExportFormatError
from uuid import uuid4

from app.domain.exceptions import PermissionDeniedError
from app.infrastructure.export.docx_exporter import DocxExporter
from app.infrastructure.export.txt_export import TxtExporter


@pytest.fixture
def export_service(document_service) -> ExportService:
    return ExportService(
        document_service=document_service,
        exporters={"txt": TxtExporter(), "docx": DocxExporter()}
    )

class TestExportDocument:

    async def test_export_as_txt(self, export_service: ExportService, document_service) -> None:
        owner_id = uuid4()
        document = await document_service.create_document(owner_id=owner_id, title="My doc")
        content, content_type, filename = await export_service.export_document(document.id, owner_id, "txt")
        assert content == b""
        assert content_type == "text/plain; charset=utf-8"
        assert filename == "My doc.txt"

    async def test_export_as_docx(self, export_service: ExportService, document_service) -> None:
        owner_id = uuid4()
        document = await document_service.create_document(owner_id=owner_id, title="Docx doc")
        content, content_type, filename = await export_service.export_document(document.id, owner_id, "docx")
        assert content[:2] == b"PK" # docx — это zip-архив. сигантура PK
        assert filename == "Docx doc.docx"

    async def test_export_unsupported_format_raises(self, export_service: ExportService, document_service) -> None:
        owner_id = uuid4()
        document = await document_service.create_document(owner_id=owner_id, title="Unsupported doc")
        with pytest.raises(UnsupportedExportFormatError):
            await export_service.export_document(document.id, owner_id, "pdf")


    async def test_export_without_permission_raises(self, export_service: ExportService, document_service) -> None:
        owner_id = uuid4()
        stranger_id = uuid4()
        document = await document_service.create_document(owner_id=owner_id, title="Private doc")
        with pytest.raises(PermissionDeniedError):
            await export_service.export_document(document.id, stranger_id, "txt")