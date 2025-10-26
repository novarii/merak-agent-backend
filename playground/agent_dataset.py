"""Shared agent dataset used for file generation and Supabase seeding."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Callable, List

try:  # Allow running via `python playground/...` and as a package.
    from playground.raw_agent_data import DEMO_LINK_ID, _RAW_AGENT_DATA
except ImportError:  # pragma: no cover
    from raw_agent_data import DEMO_LINK_ID, _RAW_AGENT_DATA  # type: ignore


@dataclass(frozen=True)
class Endorsement:
    endorser_name: str
    endorsement_text: str
    endorser_role: str | None = None


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    name: str
    tagline: str
    card_description: str
    profile_description: str
    profile_img: str
    developer: str
    highlights: List[str] = field(default_factory=list)
    demo_link: str | None = None
    base_rate: float | None = None
    success_rate: float | None = None
    experience_years: int | None = None
    availability: str | None = None
    industry: str | None = None
    agent_type: str | None = None
    languages: List[str] = field(default_factory=list)
    endorsements: List[Endorsement] = field(default_factory=list)


_AGENT_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "merak-agents")
_RNG_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "merak-agent-rng")

# Static demo video identifiers used across agent payloads.
# Available avatar assets sourced from assets/profile/logos.
PROFILE_IMG_POOL = [f"logoipsum-{idx}.svg" for idx in range(1, 12)]

AVAILABILITY_OPTIONS = ("full-time", "part-time", "contract")
AGENT_TYPE_OPTIONS = ("voice", "text", "multimodal")

HighlightFactory = Callable[[random.Random], str]


def _rng_for(agent_id: str, salt: str) -> random.Random:
    """Derive a deterministic RNG seeded from the agent identifier."""

    seed = uuid.uuid5(_RNG_NAMESPACE, f"{agent_id}:{salt}").int
    return random.Random(seed)


def _percentage_stat(low: int, high: int, suffix: str) -> HighlightFactory:
    def _factory(rng: random.Random) -> str:
        return f"{rng.randint(low, high)}% {suffix}"

    return _factory


def _multiplier_stat(low: float, high: float, suffix: str) -> HighlightFactory:
    def _factory(rng: random.Random) -> str:
        return f"{rng.uniform(low, high):.1f}x {suffix}"

    return _factory


_HIGHLIGHT_FACTORIES: List[HighlightFactory] = [
    _percentage_stat(95, 99, "accuracy rate"),
    _multiplier_stat(1.8, 3.6, "faster response"),
    _percentage_stat(93, 99, "task completion"),
    (lambda rng: f"{rng.uniform(99.4, 99.9):.1f}% uptime"),
    _multiplier_stat(3.0, 4.5, "ROI increase"),
    _percentage_stat(85, 95, "cost reduction"),
    _multiplier_stat(3.5, 4.8, "productivity gain"),
    _percentage_stat(94, 99, "customer satisfaction"),
    (lambda rng: f"Handles {rng.randint(200, 500)}+ edge cases"),
    (lambda rng: f"{rng.randint(30, 60)}+ integrations"),
    (lambda rng: f"Supports {rng.randint(12, 20)} languages"),
    (lambda rng: "24/7 availability"),
    (lambda rng: f"{rng.randint(1, 3)}M+ transactions/month"),
    (lambda rng: f"{rng.randint(400, 700)}K+ queries handled"),
    (lambda rng: f"{rng.randint(95, 140)}+ industry templates"),
    (lambda rng: f"Processes {rng.randint(10, 25)}K+ daily"),
    (lambda rng: f"{rng.randint(95, 100)} NPS score"),
    (lambda rng: f"{rng.uniform(4.7, 5.0):.1f}/5 user rating"),
    _percentage_stat(90, 98, "first-contact fix"),
    (lambda rng: "ISO certified"),
    (lambda rng: "HIPAA compliant"),
    (lambda rng: "SOC 2 certified"),
    (lambda rng: f"{rng.randint(4, 8)} years proven track"),
    (lambda rng: "Zero data breaches"),
]


def _make_agent_id(name: str) -> str:
    return str(uuid.uuid5(_AGENT_ID_NAMESPACE, name.strip().lower()))


def _random_profile_img(rng: random.Random) -> str:
    """Return a random logo asset name for agent profile cards."""

    return rng.choice(PROFILE_IMG_POOL)


def _random_availability(rng: random.Random) -> str:
    """Pick an availability value from the admissible pool."""

    return rng.choice(AVAILABILITY_OPTIONS)


def _random_agent_type(rng: random.Random) -> str:
    """Pick an agent type value from the admissible pool."""

    return rng.choice(AGENT_TYPE_OPTIONS)


def _generate_highlights(rng: random.Random, count: int = 3) -> List[str]:
    """Create a set of marketing highlights with sensible performance floors."""

    sample_size = min(count, len(_HIGHLIGHT_FACTORIES))
    selections = rng.sample(_HIGHLIGHT_FACTORIES, k=sample_size)
    return [factory(rng) for factory in selections]


def get_agent_records() -> List[AgentProfile]:
    records: List[AgentProfile] = []
    for payload in _RAW_AGENT_DATA:
        agent_id = _make_agent_id(payload["name"])
        endorsements = [
            Endorsement(
                endorser_name=item["endorser_name"],
                endorsement_text=item["endorsement_text"],
                endorser_role=item.get("endorser_role"),
            )
            for item in payload.get("endorsements", ())
        ]
        highlight_values = payload.get("highlights")
        highlights = (
            list(highlight_values)
            if highlight_values is not None
            else _generate_highlights(_rng_for(agent_id, "highlights"))
        )
        availability = payload.get("availability")
        if availability not in AVAILABILITY_OPTIONS:
            availability = _random_availability(
                _rng_for(agent_id, "availability")
            )
        agent_type = payload.get("agent_type")
        if agent_type not in AGENT_TYPE_OPTIONS:
            agent_type = _random_agent_type(_rng_for(agent_id, "agent_type"))
        profile_img = payload.get("profile_img")
        if not profile_img:
            profile_img = _random_profile_img(_rng_for(agent_id, "profile_img"))
        records.append(
            AgentProfile(
                agent_id=agent_id,
                name=payload["name"],
                tagline=payload["tagline"],
                card_description=payload["card_description"],
                profile_description=payload["profile_description"],
                profile_img=profile_img,
                developer=payload["developer"],
                highlights=highlights,
                demo_link=payload.get("demo_link"),
                base_rate=payload.get("base_rate"),
                success_rate=payload.get("success_rate"),
                experience_years=payload.get("experience_years"),
                availability=availability,
                industry=payload.get("industry"),
                agent_type=agent_type,
                languages=list(payload.get("languages", ())),
                endorsements=endorsements,
            )
        )
    return records


__all__ = ["AgentProfile", "Endorsement", "DEMO_LINK_ID", "get_agent_records"]
