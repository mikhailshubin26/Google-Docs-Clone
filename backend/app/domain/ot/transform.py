from backend.app.domain.ot.operation import Operation, OpComponent, Insert, Retain, Delete

# Приводит две операции, построенные от одной и той же ревизии документа.
def transform(op_a: Operation, op_b: Operation) -> tuple[Operation, Operation]:
    a_prime: list[OpComponent] = []
    b_prime: list[OpComponent] = []

    a_ops = list(op_a.components)
    b_ops = list(op_b.components)

    # Текущий компонент каждой из операций и остаток его длины
    a_comp, a_ops = _next(a_ops)
    b_comp, b_ops = _next(b_ops)

    while a_comp is not None and b_comp is not None:
        # Случай Insert/Insert
        if isinstance(a_comp, Insert):
            a_prime.append(a_comp)
            b_prime.append(Retain(len(a_comp.text)))
            a_comp, a_ops = _next(a_ops)
            continue

        if isinstance(b_comp, Insert):
            a_prime.append(Retain(len(b_comp.text)))
            b_prime.append(b_comp)
            b_comp, b_ops = _next(b_ops)
            continue

        # Случаи Retain/Retain; Delete/Delete; Delete/Retain; Retain/Delete;
        len_a = _length(a_comp)
        len_b = _length(b_comp)
        shared = min(len_a, len_b)

        # Обе стороны retain'ят общий кусок
        if isinstance(a_comp, Retain) and isinstance(b_comp, Retain):
            a_prime.append(Retain(shared))
            b_prime.append(Retain(shared))

        # Оба удаляют один и тот же текст
        elif isinstance(a_comp, Delete) and isinstance(b_comp, Delete):
            pass

        # A удаляет то, что B пропускает
        elif isinstance(a_comp, Delete) and isinstance(b_comp, Retain):
            a_prime.append(Delete(shared))

        # A проускает, B удаляет
        elif isinstance(a_comp, Retain) and isinstance(b_comp, Delete):
            b_prime.append(Delete(shared))

        a_comp, a_ops = _consume(a_comp, shared, a_ops)
        b_comp, b_ops = _consume(b_comp, shared, b_ops)

    a_result = Operation(
        components=tuple(_merge(a_prime)),
        client_id=op_a.client_id,
        base_revision=op_b.base_revision + 1,
    )

    b_result = Operation(
        components=tuple(_merge(b_prime)),
        client_id=op_b.client_id,
        base_revision=op_a.base_revision + 1,
    )
    return a_result, b_result


# Достаёт следующий компонент из очереди, если она не пуста
def _next(ops: list[Operation]) -> tuple[OpComponent | None, list[OpComponent]]:
    if not ops:
        return None, ops
    return ops[0], ops[1:]

# Возвращает длину компонента (сколько символов документа он затрагивает)
def _length(comp: Operation) -> int:
    if isinstance(comp, Retain):
        return comp.count
    if isinstance(comp, Delete):
        return comp.count
    raise ValueError(f"Insert has no length in this context")

# Отраезает amount символов от компонента; если он исчерпан — берёт следующий компонент
def _consume(comp: OpComponent, amount: int, remaining_ops: list[OpComponent]) -> tuple[OpComponent | None, list[OpComponent]]:
    left = _length(comp) - amount
    if left > 0:
        new_comp = Retain(left) if isinstance(comp, Retain) else Delete(left)
        return new_comp, remaining_ops
    return _next(remaining_ops)

# Склеивает соседние компоненты одного типа
def _merge(components: list[OpComponent]) -> list[OpComponent]:
    if not components:
        return []

    merged = [components[0]]
    for comp in components[1:]:
        last = merged[-1]
        if isinstance(comp, Retain) and isinstance(last, Retain):
            merged[-1] = Retain(last.count + comp.count)
        elif isinstance(comp, Delete) and isinstance(last, Delete):
            merged[-1] = Delete(last.count + comp.count)
        elif isinstance(comp, Insert) and isinstance(last, Insert):
            merged[-1] = Insert(last.text + comp.text)
        else:
            merged.append(comp)

    return merged