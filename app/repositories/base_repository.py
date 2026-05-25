from typing import Generic, Optional, Type, TypeVar

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
