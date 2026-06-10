from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.seguridad import RefreshToken
from app.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: Session):
        super().__init__(session, RefreshToken)

    def create(
        self, usuario_id: int, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        rt = RefreshToken(
            usuario_id=usuario_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(rt)
        self.session.flush()
        return rt

    def get_valido(self, token_hash: str) -> Optional[RefreshToken]:
        rt = self.session.exec(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        ).first()
        if not rt or rt.revoked:
            return None
        # comparacion tz-aware (expires_at se guarda en utc)
        expira = rt.expires_at
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)
        if expira < datetime.now(timezone.utc):
            return None
        return rt

    def revoke(self, rt: RefreshToken) -> None:
        rt.revoked = True
        self.session.add(rt)

    def revoke_by_hash(self, token_hash: str) -> None:
        rt = self.session.exec(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        ).first()
        if rt and not rt.revoked:
            rt.revoked = True
            self.session.add(rt)
