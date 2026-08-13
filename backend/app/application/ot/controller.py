from app.domain.exceptions import DocumentNotFoundError, OperationConflictError
from app.domain.ot.operation import Operation
from app.domain.repositories.document import DocumentRepository
from app.domain.repositories.operation_log import OperationLogRepository
from app.domain.ot.apply import apply
from app.domain.ot.transform import transform

from uuid import UUID

"""
Серверный OT-контроллер Отвечает за:
1) Приём операции от клиента вместе с revision, от которой она построена;
2) Трансформацию этой операции против всех операций, случившихся позже;
3) Применение результата к документу и увеличение revision;
4) Сохранение операции в лог
"""
class OTController:
    def __init__(
            self,
            document_repo: DocumentRepository,
            operation_log_repo: OperationLogRepository,
            compact_threshold: int,
    ) -> None:
        self._document_repo = document_repo
        self._operation_log_repo = operation_log_repo
        self._compact_threshold = compact_threshold

    # Схлопывает лог операций, если накопилось больше threshold записей
    async def _maybe_compact(self, document_id: UUID, current_revision: int) -> None:
        latest_logged_revision = await self._operation_log_repo.get_latest_revision(document_id)
        if latest_logged_revision >= self._compact_threshold:
            await self._operation_log_repo.compact(document_id, current_revision)

    # Возвращает актуальный текст документа и его ревизию, собирая их из последнего снапшота;
    async def get_current_state(self, document_id: UUID) -> tuple[str, int]:
        document = await self._document_repo.get_by_id(document_id)
        if document is None or document.is_deleted():
            raise DocumentNotFoundError(document_id)

        pending_ops = await self._operation_log_repo.get_operations_since(document_id, document.revision)

        content = document.content_snapshot
        revision = document.revision
        for op in pending_ops:
            content = apply(content, op)
            revision += 1

        return content, revision

    # Применяет операцию клиента
    async def submit_operation(self, document_id: UUID, operation: Operation) -> tuple[Operation, int]:
        content, current_revision = await self.get_current_state(document_id)

        # Операция ссылается на более позднюю ревизию (баг клиента)
        if operation.base_revision > current_revision:
            raise OperationConflictError(operation.base_revision, current_revision)

        concurrent_ops = await self._operation_log_repo.get_operations_since(document_id, current_revision)

        # Лог был схлопнут до ревизии выше
        expected_count = current_revision - operation.base_revision
        if len(concurrent_ops) < expected_count:
            raise OperationConflictError(operation.base_revision, current_revision)

        transformed_op = operation
        for concurrent_op in concurrent_ops:
            transformed_op, _ = transform(transformed_op, concurrent_op)

        new_content = apply(content, transformed_op)
        new_revision = current_revision + 1

        await self._operation_log_repo.append(document_id, new_revision, transformed_op)

        document = await self._document_repo.get_by_id(document_id)
        if document is None or document.is_deleted():
            raise DocumentNotFoundError(document_id)

        # Обновляем снапшот в Postgres
        document.apply_snapshot(new_content, new_revision)
        await self._document_repo.update(document)
        await self._maybe_compact(document_id, new_revision)

        return transformed_op, new_revision