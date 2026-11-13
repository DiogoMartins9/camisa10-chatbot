
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
from sqlalchemy.dialects.postgresql import UUID, JSONB
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

class PerguntaQuiz(Base):
    __tablename__ = "perguntas_quiz"

    __table_args__ = (
        UniqueConstraint(
            "quiz_id",
            "ordem",
            name="uq_pergunta_quiz_ordem",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    alternativas: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False
    )
    resposta_correta: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    explicacao: Mapped[str] = mapped_column(Text, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)


class TentativaQuiz(Base):
    __tablename__ = "tentativas_quiz"

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
    acertos: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    pontuacao: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    xp_total: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    finalizada: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    iniciada_em: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    finalizada_em: Mapped[DateTime | None] = mapped_column(
        DateTime, nullable=True
    )


class RespostaQuiz(Base):
    __tablename__ = "respostas_quiz"

    __table_args__ = (
        UniqueConstraint(
            "tentativa_id",
            "pergunta_id",
            name="uq_resposta_tentativa_pergunta",
        ),
        CheckConstraint(
            "resposta_selecionada >= 0",
            name="ck_resposta_quiz_indice",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tentativa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tentativas_quiz.id", ondelete="CASCADE"),
        nullable=False,
    )
    pergunta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("perguntas_quiz.id", ondelete="CASCADE"),
        nullable=False,
    )
    resposta_selecionada: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    correta: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    xp_ganho: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    respondida_em: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )


class SequenciaQuiz(Base):
    __tablename__ = "sequencias_quiz"

    __table_args__ = (
        CheckConstraint(
            "sequencia_atual >= 0",
            name="ck_sequencia_atual",
        ),
        CheckConstraint(
            "maior_sequencia >= 0",
            name="ck_maior_sequencia",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    sequencia_atual: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    maior_sequencia: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    ultima_participacao: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
    )

    criado_em: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
