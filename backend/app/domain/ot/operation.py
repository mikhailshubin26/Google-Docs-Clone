from dataclasses import dataclass

"""
Модель операции для Operational Transformation.

Операция — это список компонентов (Retain/Insert/Delete), которые
применяются последовательно к тексту документа слева направо.
"""

@dataclass(frozen=True)
class Retain:
    # Пропустить count символов, не изменяя их
    count: int

    def __post_init__(self) -> None:
        if self.count <= 0:
            raise ValueError("Retain count must be positive")

@dataclass(frozen=True)
class Insert:
    # Вставить строку text в текущую позицию
    text: str

    def __post_init__(self) -> None:
        if self.text == "":
            raise ValueError("Insert text must be non-empty")

@dataclass(frozen=True)
class Delete:
    # Удалить count символов, начиная с текущей позиции
    count: int

    def __post_init__(self) -> None:
        if self.count <= 0:
            raise ValueError("Delete count must be positive")

# Компонент операции — один из трёх вариантов
OpComponent = Retain | Insert | Delete

@dataclass(frozen=True)
class Operation:
    """
    Полная операция: упорядоченный список компонентов плюс метаданные
    об авторе и ревизии, к которой она была применена на клиенте
    """
    components: tuple[OpComponent, ...]
    client_id: str
    base_revision: int

    # Считает, на сколько символов изменится длина документа после редактирования
    def target_length_delta(self) -> int:
        delta = 0
        for comp in self.components:
            if isinstance(comp, Insert):
                delta += len(comp.text)
            elif isinstance(comp, Delete):
                delta -= comp.count
        return delta

    # Считает, какой длины должен быть документ ДО операции
    def base_length(self) -> int:
        length = 0
        for comp in self.components:
            if isinstance(comp, Retain) or isinstance(comp, Delete):
                length += comp.count
        return length