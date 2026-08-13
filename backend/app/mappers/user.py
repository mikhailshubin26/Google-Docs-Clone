from app.domain.entities.user import User
from app.infrastructure.db.models.user import UserModel

# Собирает доменную сущность User из строки таблицы users
def user_model_to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        display_name=model.display_name,
        is_guest=model.is_guest,
        created_at=model.created_at,
        email=model.email,
        password_hash=model.password_hash,
    )

# Создаёт новую ORM-модель из доменной сущности (Испоользуется при создании нового пользователя)
def user_entity_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        display_name=user.display_name,
        is_guest=user.is_guest,
        created_at=user.created_at,
        email=user.email,
        password_hash=user.password_hash,
    )

# Перенести изменившиеся поля сущности в уже существующую ORM-модель
def apply_user_entity_to_model(user: User, model: UserModel) -> None:
    model.display_name = user.display_name
    model.is_guest = user.is_guest
    model.email = user.email
    model.password_hash = user.password_hash
    # id и created_at неизменяемы!