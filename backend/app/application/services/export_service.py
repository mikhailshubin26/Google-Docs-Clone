from uuid import UUID

from app.application.interfaces.exporter import Exporter
from app.application.services.document_service import DocumentService
from app.domain.exceptions import DocumentNotFoundError

# Запрошен формат, для которого нет зарегистрированного Exporter'а
class UnsupportedExportFormatError(Exception):
    def __init__(self, format_name: str):
        self.format_name = format_name
        super().__init__(f"Unsupported export format: {format_name!r}")

# Бизнес-логика экспорта документов
class ExportService:
    def __init__(self, document_service: DocumentService, exporters: dict[str, Exporter]):
        self._document_service = document_service
        self._exporters = exporters

    async def export_document(
            self,
            document_id: UUID,
            user_id: UUID,
            format_name: str
    ) -> tuple[bytes, str, str]: # Возвращаем кортеж (содержимое, MIME-тип, название)
        exporter = self._exporters.get(format_name)
        if exporter is None:
            raise UnsupportedExportFormatError(format_name)

        document = await self._document_service.get_document(document_id, user_id)
        content = exporter.export(document)
        filename = f"{document.title}.{exporter.file_extension}"
        return content, exporter.content_type, filename