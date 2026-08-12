from backend.app.domain.ot.operation import Operation, Retain, Delete, Insert
from backend.app.domain.exceptions import InvalidOperationError


# Применяет операцию к тексту документа и возвращает новый текст
def apply(document_text: str, operation: Operation) -> str:
    if operation.base_length() != len(document_text):
        raise InvalidOperationError(f"Operation excepts document length: {operation.base_length()}, got {len(document_text)}")

    result: list[str] = []
    cursor = 0

    for comp in operation.components:
        if isinstance(comp, Retain):
            result.append(document_text[cursor:cursor + comp.count])
            cursor += comp.count
        elif isinstance(comp, Insert):
            result.append(comp.text)
        elif isinstance(comp, Delete):
            cursor += comp.count

    return "".join(result)

