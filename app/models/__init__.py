from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Investigation(Base):
    __tablename__ = "investigation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="in_progress", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    step_count: Mapped[int] = mapped_column(Integer, default=0)
    budget: Mapped[int] = mapped_column(Integer, default=4)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    artifacts: Mapped[list[Artifact]] = relationship(back_populates="investigation")
    evidence: Mapped[list[Evidence]] = relationship(back_populates="investigation")
    hypotheses: Mapped[list[Hypothesis]] = relationship(back_populates="investigation")
    requests: Mapped[list[EvidenceRequest]] = relationship(back_populates="investigation")


class Artifact(Base):
    __tablename__ = "artifact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigation.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    raw_text: Mapped[str] = mapped_column(Text)
    redaction_map: Mapped[str] = mapped_column(Text, default="{}")
    source_meta: Mapped[str] = mapped_column(Text, default="{}")

    investigation: Mapped[Investigation] = relationship(back_populates="artifacts")
    evidence: Mapped[list[Evidence]] = relationship(back_populates="artifact")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigation.id"), index=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifact.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    span_start: Mapped[int] = mapped_column(Integer)
    span_end: Mapped[int] = mapped_column(Integer)
    normalized_text: Mapped[str] = mapped_column(Text)
    signal_tags: Mapped[str] = mapped_column(Text, default="[]")
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

    investigation: Mapped[Investigation] = relationship(back_populates="evidence")
    artifact: Mapped[Artifact] = relationship(back_populates="evidence")
    links: Mapped[list[EvidenceLink]] = relationship(back_populates="evidence")


class Hypothesis(Base):
    __tablename__ = "hypothesis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigation.id"), index=True)
    category: Mapped[str] = mapped_column(String(64))
    statement: Mapped[str] = mapped_column(Text)
    novelty_score: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="active")

    investigation: Mapped[Investigation] = relationship(back_populates="hypotheses")
    links: Mapped[list[EvidenceLink]] = relationship(back_populates="hypothesis")


class EvidenceLink(Base):
    __tablename__ = "evidence_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("hypothesis.id"), index=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence.id"), index=True)
    relation: Mapped[str] = mapped_column(String(16))
    strength: Mapped[str] = mapped_column(String(16))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rationale: Mapped[str] = mapped_column(Text, default="")

    hypothesis: Mapped[Hypothesis] = relationship(back_populates="links")
    evidence: Mapped[Evidence] = relationship(back_populates="links")


class EvidenceRequest(Base):
    __tablename__ = "evidence_request"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigation.id"), index=True)
    hypothesis_id: Mapped[int | None] = mapped_column(ForeignKey("hypothesis.id"), nullable=True)
    what: Mapped[str] = mapped_column(Text)
    why: Mapped[str] = mapped_column(Text)
    expected_signal: Mapped[str] = mapped_column(Text)
    format: Mapped[str] = mapped_column(String(64), default="log, trace, config, or command output")

    investigation: Mapped[Investigation] = relationship(back_populates="requests")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigation.id"), index=True)
    chosen_root_cause: Mapped[str] = mapped_column(Text)
    was_correct: Mapped[bool] = mapped_column(Boolean)
    resolution_note: Mapped[str] = mapped_column(Text, default="")


class ResolvedIncident(Base):
    __tablename__ = "resolved_incident"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigation.id"), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    chosen_root_cause: Mapped[str] = mapped_column(Text)
    resolution_note: Mapped[str] = mapped_column(Text, default="")
    symptom_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RootCausePattern(Base):
    __tablename__ = "root_cause_pattern"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    symptom_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    summary: Mapped[str] = mapped_column(Text)
    resolution_note: Mapped[str] = mapped_column(Text, default="")
    weight: Mapped[int] = mapped_column(Integer, default=1)
