from datetime import datetime, timezone
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import func, select as sa_select
from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    # get y list base cada repo suma sus queries

    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, pk: int) -> Optional[T]:
        return self.session.get(self.model, pk)

    def list_all(self, *, skip: int = 0, limit: int = 100):
        return self.session.exec(select(self.model).offset(skip).limit(limit)).all()

    def count(self) -> int:
        stmt = sa_select(func.count()).select_from(self.model)
        return self.session.execute(stmt).scalar_one()

    # helpers genericos: flush + refresh sin commit (el commit lo hace la UoW)
    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()

    def soft_delete(self, entity: T) -> None:
        # asume que el modelo tiene campo deleted_at (datetime)
        entity.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        self.session.add(entity)
        self.session.flush()
