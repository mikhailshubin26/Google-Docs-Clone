from typing import Protocol

from app.domain.entities.document import Document


# абстрактный контракт экспортёра документа в файл
class Exporter(Protocol):

    content_type: str
    file_extension: str

    # Превращает документ в байты готового файла
    def export(self, document: Document) -> bytes:
        ...