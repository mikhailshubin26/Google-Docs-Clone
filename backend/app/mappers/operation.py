import json
from app.domain.ot.operation import Operation, OpComponent, Retain, Insert, Delete

# превращает один компонент операции в JSON-совместимый словарь
def _component_to_dict(comp: OpComponent) -> dict:
    if isinstance(comp, Retain):
        return {"type": "retain", "count": comp.count}
    if isinstance(comp, Insert):
        return {"type": "insert", "text": comp.text}
    if isinstance(comp, Delete):
        return {"type": "delete", "count": comp.count}
    raise ValueError(f"Unknown operation component: {comp!r}")

# восстанавливает компонент операции из словаря
def _component_from_dict(data: dict) -> OpComponent:
    comp_type = data["type"]
    if comp_type == "retain":
        return Retain(count=data["count"])
    if comp_type == "insert":
        return Insert(text=data["text"])
    if comp_type == "delete":
        return Delete(count=data["count"])
    raise ValueError(f"Unknown operation component: {comp_type!r}")

# Сериализует operation в словарь — используется в WS
def operation_to_dict(operation: Operation) -> dict:
    return {
        "components": [_component_to_dict(c) for c in operation.components],
        "client_id": operation.client_id,
        "base_revision": operation.base_revision,
    }

# Десереализует dict в Operation
def operation_from_dict(data: dict) -> Operation:
    components = tuple(_component_from_dict(c) for c in data["components"])
    return Operation(
        components=components,
        client_id=data["client_id"],
        base_revision=data["base_revision"],
    )


def operation_to_json(operation: Operation) -> str:
    data = {
        "components": [_component_to_dict(c) for c in operation.components],
        "client_id": operation.client_id,
        "base_revision": operation.base_revision,
    }
    return json.dumps(data)

# преваращет json в operation
def operation_from_json(raw: str) -> Operation:
    data = json.loads(raw)
    components = tuple(_component_from_dict(c) for c in data["components"])
    return Operation(components=components, client_id=data["client_id"], base_revision=data["base_revision"])