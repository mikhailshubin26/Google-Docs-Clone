from app.domain.ot.apply import apply
from app.domain.ot.operation import Operation, Retain, Insert, Delete
from app.domain.ot.transform import transform


# Юнит-тесты transform() — ручные edge-кейсы конкурентных операций,
# построенных от одной и той же ревизии документа.

def _op(components: tuple, client_id: str = "client", base_revision: int = 0) -> Operation:
    return Operation(components=components, client_id=client_id, base_revision=base_revision)

# Проверка сходимости для пары конкурентных операций
def _assert_converges(document: str, op_a: Operation, op_b: Operation) -> None:
    a_prime, b_prime = transform(op_a, op_b)

    result_via_a_first = apply(apply(document, op_a), b_prime)
    result_via_b_first = apply(apply(document, op_b), a_prime)

    assert result_via_a_first == result_via_b_first

# Тестирование оновременной вставки со стороны двух клиентов
class TestTransformInsertInsert:

    # "Hello world": A вставляет "!" в конец, B вставляет "," после "Hello"
    def test_inserts_at_different_position(self):
        document = "Hello world"
        op_a = _op((Retain(11), Insert("!")), client_id="A")
        op_b = _op((Retain(5), Insert(","), Retain(6)), client_id="B")
        _assert_converges(document, op_a, op_b)

    # Оба клиента вставляют разный текст в одну и ту же позицию (5)
    def test_inserts_at_same_position(self):
        document = "Hello world"
        op_a = _op((Retain(5), Insert(" beautiful"), Retain(6)), client_id="A")
        op_b = _op((Retain(5), Insert(" cruel"), Retain(6)), client_id="B")
        _assert_converges(document, op_a, op_b)

    # Оба клиента вставляют разный текст в начало
    def test_inserts_at_start(self):
        document = "world"
        op_a = _op((Insert("Hello "), Retain(5)), client_id="A")
        op_b = _op((Insert("Beautiful "), Retain(5)), client_id="B")
        _assert_converges(document, op_a, op_b)

# Тестирование одновременного удаления со стороны двух клиентов
class TestTransformDeleteDelete:

    # Пользовательские удаления не затрагивают друг-друга
    def test_no_overlapping_deletes(self):
        document = "Hello world"
        op_a = _op((Delete(5), Retain(6)), client_id="A")
        op_b = _op((Retain(6), Delete(5)), client_id="B")
        _assert_converges(document, op_a, op_b)

    # Оба клиента удаляют один и тот же диапазон целиком
    def test_fully_overlapping_deletes(self):
        document = "Hello world"
        op_a = _op((Retain(6), Delete(5)), client_id="A")
        op_b = _op((Retain(6), Delete(5)), client_id="B")
        _assert_converges(document, op_a, op_b)

    # Удаления клиентов частично накладываются друг на друга
    def test_partially_overlapping_deletes(self):
        document = "Hello world"
        op_a = _op((Delete(6), Retain(5)), client_id="A")
        op_b = _op((Retain(3), Delete(5), Retain(3)), client_id="B")
        _assert_converges(document, op_a, op_b)

# Тестирование, когда один клиент вставляет текст, а другой удаляет
class TestTransformInsertDelete:

    # Вставка текста в зону удаления
    def test_inserts_inside_deleted_range(self):
        document = "Hello world"
        op_a = _op((Delete(11),), client_id="A")
        op_b = _op((Retain(5), Insert(" my"), Retain(6)), client_id="B")
        _assert_converges(document, op_a, op_b)

    # Текст вставляется до зоны удаления
    def test_inserts_before_deleted_range(self):
        document = "Hello world"
        op_a = _op((Insert("Well, "), Retain(11)), client_id="A")
        op_b = _op((Retain(6), Delete(5)), client_id="B")
        _assert_converges(document, op_a, op_b)

    def test_inserts_after_deleted_range(self):
        document = "Hello world"
        op_a = _op((Retain(11), Insert("!"),), client_id="A")
        op_b = _op((Delete(6), Retain(5)), client_id="B")
        _assert_converges(document, op_a, op_b)

# Тестирование отсутствия операций со стороны клиентов
class TestTransformNoOp:

    # Обе операции ничего не меняют
    def test_identical_retain_only_opperations(self):
        document = "Hello world"
        op_a = _op((Retain(11),), client_id="A")
        op_b = _op((Retain(11),), client_id="B")
        _assert_converges(document, op_a, op_b)