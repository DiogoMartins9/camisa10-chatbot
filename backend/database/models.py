
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    google_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    senha_hash: Mapped[str] = mapped_column(Text, nullable=False)
    data_nascimento: Mapped[Date | None] = mapped_column(Date)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )


class Perfil(Base):
    __tablename__ = "perfis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    apelido: Mapped[str | None] = mapped_column(String(50))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    time_coracao_id: Mapped[str | None] = mapped_column(String(100))
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )


class Favorito(Base):
    __tablename__ = "favoritos"

    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "tipo_item", "item_id",
            name="uq_favorito_usuario_item",
        ),
        CheckConstraint(
            "tipo_item IN ('time', 'jogador')",
            name="ck_favoritos_tipo_item",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tipo_item: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )


class ConfiguracaoAcessibilidade(Base):
    __tablename__ = "configuracoes_acessibilidade"

    __table_args__ = (
        CheckConstraint(
            "tamanho_fonte IN ('pequeno', 'medio', 'grande', 'extra_grande')",
            name="ck_acessibilidade_tamanho_fonte",
        ),
        CheckConstraint(
            "daltonismo IN ('nenhum', 'protanopia', 'deuteranopia', 'tritanopia')",
            name="ck_acessibilidade_daltonismo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    tamanho_fonte: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="medio"
    )
    alto_contraste: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    reduzir_animacoes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    daltonismo: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="nenhum"
    )
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    codigo: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(100))
    total_perguntas: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )


class ProgressoJogo(Base):
    __tablename__ = "progresso_jogos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    pontuacao: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    acertos: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    tentativas: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    concluido: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    ultima_participacao: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
