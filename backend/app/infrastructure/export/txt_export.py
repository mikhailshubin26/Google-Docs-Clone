from app.domain.entities.document import Document

# Экспорт документа в txt файл

class TxtExporter:
    content_type = "text/plain; charset=utf-8"
    file_extension = "txt"

    # Превращает документ в байты готового файла
    def export(self, document: Document) -> bytes:
        return document.content_snapshot.encode("utf-8")