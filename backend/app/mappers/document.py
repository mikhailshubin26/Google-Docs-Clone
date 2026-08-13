from app.domain.entities.document import Document
from app.infrastructure.db.models.document import DocumentModel

# Собирает доменную сущность Document из строки таблицы documents
def document_model_to_entity(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        owner_id=model.owner_id,
        title=model.title,
        content_snapshot=model.content_snapshot,
        revision=model.revision,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )

# Создаёт новую ORM-модель документа из доменной сущности документа
def document_entity_to_model(document: Document) -> DocumentModel:
    return DocumentModel(
        id=document.id,
        owner_id=document.owner_id,
        title=document.title,
        content_snapshot=document.content_snapshot,
        revision=document.revision,
        created_at=document.created_at,
        updated_at=document.updated_at,
        deleted_at=document.deleted_at,
    )

# Перенести изменившиеся поля сущности в уже существующую ORM-модель
def apply_document_entity_to_model(document: Document, model: DocumentModel) -> None:
    model.title = document.title
    model.content_snapshot = document.content_snapshot
    model.revision = document.revision
    model.updated_at = document.updated_at
    model.deleted_at = document.deleted_at
    #id, owner_id и created_at неизменяемы!