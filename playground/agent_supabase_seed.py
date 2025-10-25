"""Utility script that seeds Supabase tables with local agent metadata."""

from __future__ import annotations

import json
import os
import uuid
from typing import Dict, Iterable, List

from urllib import error, request, parse
from dotenv import load_dotenv

from agent_dataset import AgentProfile, get_agent_records


_ENDORSEMENT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "merak-agent-endorsements")


def _env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def _build_agent_payload(records: Iterable[AgentProfile]) -> List[Dict[str, object]]:
    payload: List[Dict[str, object]] = []
    for record in records:
        payload.append(
            {
                "id": record.agent_id,
                "name": record.name,
                "tagline": record.tagline,
                "card_description": record.card_description,
                "profile_img": record.profile_img,
                "profile_description": record.profile_description,
                "developer": record.developer,
                "highlights": list(record.highlights),
                "demo_link": record.demo_link,
                "base_rate": record.base_rate,
                "success_rate": record.success_rate,
                "experience_years": record.experience_years,
                "availability": record.availability,
                "industry": record.industry,
                "agent_type": record.agent_type,
                "languages": list(record.languages),
            }
        )
    return payload


def _build_endorsement_payload(records: Iterable[AgentProfile]) -> List[Dict[str, object]]:
    payload: List[Dict[str, object]] = []
    for record in records:
        for item in record.endorsements:
            endorsement_id = uuid.uuid5(
                _ENDORSEMENT_NAMESPACE,
                f"{record.agent_id}:{item.endorser_name.strip().lower()}",
            )
            payload.append(
                {
                    "id": str(endorsement_id),
                    "agent_id": record.agent_id,
                    "endorser_name": item.endorser_name,
                    "endorser_role": item.endorser_role,
                    "endorsement_text": item.endorsement_text,
                }
            )
    return payload


def _upsert(table: str, rows: List[Dict[str, object]], *, url: str, headers: Dict[str, str]) -> None:
    if not rows:
        print(f"→ No rows to upsert for table '{table}' – skipping.")
        return

    payload = json.dumps(rows).encode("utf-8")
    query = parse.urlencode({"on_conflict": "id"})
    req = request.Request(
        url=f"{url}/rest/v1/{table}?{query}",
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            status = resp.status
            resp.read()  # Drain to allow HTTP reuse.
    except error.HTTPError as exc:
        raise RuntimeError(
            f"Supabase upsert failed for table '{table}' ({exc.code}): {exc.read().decode()}"
        ) from exc

    print(f"✓ Upserted {len(rows)} row(s) into '{table}' (status {status}).")


def main() -> None:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env.local"))

    supabase_url = _env("SUPABASE_URL")
    supabase_service_key = _env("SUPABASE_SERVICE_ROLE_KEY")

    headers = {
        "apikey": supabase_service_key,
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    records = get_agent_records()
    if not records:
        raise RuntimeError("No agent records found – update agent_dataset.py first.")

    agent_rows = _build_agent_payload(records)
    endorsement_rows = _build_endorsement_payload(records)

    _upsert("agent_profiles", agent_rows, url=supabase_url, headers=headers)
    _upsert("endorsements", endorsement_rows, url=supabase_url, headers=headers)


if __name__ == "__main__":
    main()
