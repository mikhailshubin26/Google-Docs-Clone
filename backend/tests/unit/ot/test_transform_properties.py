from hypothesis import given, settings, strategies as st

from app.domain.ot.apply import apply
from app.domain.ot.operation import Operation, OpComponent, Insert, Retain, Delete
from app.domain.ot.transform import transform

# Генерация случайных пар конкурентных операций

# Ограничиваем алфавит и длины, чтобы работало быстрее
_TEXT_ALPHABET = st.text(alphabet='abcXYZ', min_size=1, max_size=5)

# Генерирует случайный документ и две операции
@st.composite
def _document_and_operation_pair(draw) -> tuple[str, Operation, Operation]:
    document = draw(st.text(alphabet="abcdefXYZ", min_size=0, max_size=15))

    op_a = draw(_operation_for_document(document, "A"))
    op_b = draw(_operation_for_document(document, "B"))

    return document, op_a, op_b

# Генерирует случайную (но валидную) операцию для заданного документа
@st.composite
def _operation_for_document(draw, document: str, client_id: str) -> Operation:
    components: list[OpComponent] = []
    remaining = len(document)

    while remaining > 0:
        action = draw(st.sampled_from(["retain", "insert", "delete"]))
        if action == "insert":
            components.append(Insert(draw(_TEXT_ALPHABET)))
            continue

        chunk = draw(st.integers(min_value=1, max_value=remaining))
        if action == "retain":
            components.append(Retain(chunk))
        else:
            components.append(Delete(chunk))
        remaining -= chunk

    if draw(st.booleans()):
        components.append(Insert(draw(_TEXT_ALPHABET)))

    if not components:
        components.append(Insert(draw(_TEXT_ALPHABET)))

    return Operation(components=tuple(components), client_id=client_id, base_revision=0)


@given(_document_and_operation_pair())
@settings(max_examples=300)
def test_transform_converges(data: tuple[str, Operation, Operation]) -> None:
    document, op_a, op_b = data

    a_prime, b_prime = transform(op_a, op_b)

    result_via_a_first = apply(apply(document, op_a), b_prime)
    result_via_b_first = apply(apply(document, op_b), a_prime)

    assert result_via_a_first == result_via_b_first