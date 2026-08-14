# Юнит-тесты apply() — применение операции к тексту документа
import pytest

from app.domain.exceptions import InvalidOperationError
from app.domain.ot.apply import apply
from app.domain.ot.operation import Operation, Retain, Insert, Delete


def _op(components: tuple, client_id: str = "client", base_revision: int = 0) -> Operation:
    return Operation(components=components, client_id=client_id, base_revision=base_revision)

# Тестирование применения вставки
class TestApplyInsert:

    # Вставка текста в начало
    def test_insert_at_start(self):
        op = _op((Insert("Hi, "), Retain(11)))
        assert apply("Hello world", op) == "Hi, Hello world"

    # Вставка текста в конец
    def test_insert_at_end(self):
        op = _op((Retain(11), Insert("!")))
        assert apply("Hello world", op) == "Hello world!"

    # Вставка текста в середину
    def test_insert_in_middle(self):
        # "Hello world" -> "Hello, world" (запятая после "Hello")
        op = _op((Retain(5), Insert(","), Retain(6)))
        assert apply("Hello world", op) == "Hello, world"

    # Вставка текста в пустой документ
    def test_insert_into_empty_document(self):
        op = _op((Insert("first line"),))
        assert apply("", op) == "first line"

# Тестирование применения удаления
class TestApplyDelete:

    # Удаление текста из начала документа
    def test_delete_at_start(self):
        op = _op((Delete(6), Retain(5)))
        assert apply("Hello world", op) == "world"

    # Удаление текста из конца документа
    def test_delete_at_end(self):
        op = _op((Retain(5), Delete(6)))
        assert apply("Hello world", op) == "Hello"

    # Удаление текста из центра документа
    def test_delete_in_middle(self):
        op = _op((Retain(6), Delete(3), Retain(5)))
        assert apply("Hello my world", op) == "Hello world"

    # Удаление всего текста из документа
    def test_delete_entire_document(self):
        op = _op((Delete(11),))
        assert apply("Hello world", op) == ""

# Тестирование применений смешанного набора действий
class TestApplyMixed:

    # Удалить, потом вставить. (Hello World -> Hello there)
    def test_delete_then_insert(self):
        op = _op((Retain(6), Delete(5), Insert("there")))
        assert apply("Hello world", op) == "Hello there"

    # Многократные вставки и удаления (abcdef -> aXcYef)
    def test_multiple_inserts_and_deletes(self):
        op = _op((Retain(1), Delete(1), Insert("X"), Retain(1), Delete(1), Insert("Y"), Retain(2)))
        assert apply("abcdef", op) == "aXcYef"

# Тестирование правильной валидации
class TestApplyValidation:

    # Переданный документ короче длины операции
    def test_raises_when_base_length_is_shorter(self):
        op = _op((Retain(11),))
        with pytest.raises(InvalidOperationError):
            apply("Hello", op)

    # Переданный документ короче длины операции
    def test_raises_when_base_length_is_longer(self):
        op = _op((Retain(3),))
        with pytest.raises(InvalidOperationError):
            apply("Hello World", op)

    # Пустая операция над пустым документом
    def test_empty_operation_on_empty_document(self):
        op = _op(())
        assert apply("", op) == ""