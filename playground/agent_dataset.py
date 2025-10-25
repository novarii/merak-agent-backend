"""Shared agent dataset used for file generation and Supabase seeding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import random
import uuid


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

# Static demo video identifiers used across agent payloads.
DEMO_LINK_ID = "44eFf-tRiSg"

# Available avatar assets sourced from assets/profile/logos.
PROFILE_IMG_POOL = [f"logoipsum-{idx}.svg" for idx in range(1, 12)]


def _make_agent_id(name: str) -> str:
    return str(uuid.uuid5(_AGENT_ID_NAMESPACE, name.strip().lower()))


def _random_profile_img() -> str:
    """Return a random logo asset name for agent profile cards."""

    return random.choice(PROFILE_IMG_POOL)


_RAW_AGENT_DATA = (
    {
        "name": "Kalea",
        "tagline": "Sentiment and intent analysis for live chat",
        "card_description": (
            "Captures real-time customer feedback through live chat conversations and"
            " analyzes sentiment instantly. Identifies pain points, feature requests,"
            " and satisfaction trends as they happen. Turns every chat into actionable"
            " insights that help you improve your product and service."
        ),
        "profile_description": """Customer feedback shouldn't wait until someone fills out a survey. Boom captures it the moment it happens, right in the middle of live conversations.
Most companies rely on post-interaction surveys that customers ignore or rush through. By the time feedback arrives, the context is lost and the emotional truth has faded. Boom works differently. It listens to live chat interactions in real time, detecting frustration, delight, confusion, and everything in between.
When a customer mentions a missing feature during support, Boom logs it instantly. When someone expresses frustration about a checkout process, it flags the issue before the conversation even ends. When a user praises a new update, that positive signal gets captured and categorized automatically.
Support agents don't need to do anything extra. Boom runs silently in the background, analyzing tone, keywords, and patterns across thousands of conversations. It builds a living map of what customers actually care about, not what they remember caring about days later when a survey email arrives.
Companies using Boom have seen their feedback collection rate jump from 12% to over 90%. Product teams receive weekly reports highlighting the top requested features, ranked by urgency and customer sentiment. Support managers spot recurring complaints before they become major issues, often within hours instead of weeks.
The dashboard shows everything in plain language. No complex analytics degrees required. Just clear insights like "47 customers mentioned slow loading times this week" or "Checkout confusion spiked 23% after the last update." Every data point links back to the actual conversation, so context is never lost.
Boom doesn't replace surveys. It makes them unnecessary for most decisions. By the time you might send a survey, you already know what customers think because Boom heard them say it directly.
Integrated through Merak's Unified API, it connects to your chat system in minutes and starts learning immediately. Your feedback loop goes from weeks to seconds, and your product decisions start reflecting what customers actually experience, not what they vaguely recall.
Boom turns every conversation into intelligence. Real voices, real feelings, real insights captured at the moment they matter most.""",
        "developer": "Open Studios",
        "highlights": (
            "75% user retention rate",
            "Explainable AI certified",
            "9.5 NPS score",
        ),
        "demo_link": DEMO_LINK_ID,
        "base_rate": 499,
        "success_rate": 99,
        "experience_years": 4,
        "availability": "full-time",
        "industry": "customer development",
        "agent_type": "multimodal",
        "languages": ("English"),
        "endorsements": (
            {
                "endorser_name": "Rachel Goldstein",
                "endorser_role": "Head of Support Operations, Salesforce",
                "endorsement_text": (
                    "Kalea transformed how our agents handle difficult conversations by showing them"
                    " emotional shifts before they become escalations."
                ),
            },
            {
                "endorser_name": "David Levy",
                "endorser_role": "Director of Customer Experience, HubSpot",
                "endorsement_text": (
                    "We've reduced churn by nearly 30% since Kalea started flagging at-risk customers"
                    " during live chats, giving us time to turn things around."
                ),
            },
            {
                "endorser_name": "Sarah Cohen",
                "endorser_role": "VP of Customer Success, Zendesk",
                "endorsement_text": (
                    "Kalea helped our team identify upsell opportunities we didn't even know existed,"
                    " boosting our support-driven revenue by 22% in six months."
                ),
            },
        ),
    },
)


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
        records.append(
            AgentProfile(
                agent_id=agent_id,
                name=payload["name"],
                tagline=payload["tagline"],
                card_description=payload["card_description"],
                profile_description=payload["profile_description"],
                profile_img=payload.get("profile_img", _random_profile_img()),
                developer=payload["developer"],
                highlights=list(payload.get("highlights", ())),
                demo_link=payload.get("demo_link"),
                base_rate=payload.get("base_rate"),
                success_rate=payload.get("success_rate"),
                experience_years=payload.get("experience_years"),
                availability=payload.get("availability"),
                industry=payload.get("industry"),
                agent_type=payload.get("agent_type"),
                languages=list(payload.get("languages", ())),
                endorsements=endorsements,
            )
        )
    return records


__all__ = ["AgentProfile", "Endorsement", "get_agent_records"]
