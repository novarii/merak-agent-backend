"""Raw agent payload definitions used by playground utilities."""

from __future__ import annotations


DEMO_LINK_ID = "44eFf-tRiSg"

DEMO_LINK_ID = "DEMO_LINK_ID"

_RAW_AGENT_DATA = (
    {
        "name": "Procure",
        "tagline": "Vendor performance analytics and procurement optimization",
        "card_description": (
            "Analyzes vendor performance, pricing, and supply reliability to optimize"
            " procurement decisions. Identifies cost reduction opportunities and supply"
            " risks. Negotiates better terms automatically. Reduces procurement costs by"
            " 22%, improves on-time delivery by 38%, and increases supplier diversity."
        ),
        "profile_description": """Companies overpay for goods and services while accepting poor supplier performance. Procure fixes both.
Most procurement is transactional—purchase orders get issued to established vendors at standard terms. Vendor performance is rarely tracked systematically. Cost benchmarking is infrequent. Contract negotiations happen at renewal, not strategically. Alternative suppliers aren't explored because switching is disruptive. Supplier consolidation happens through inertia, not analysis. Meanwhile, costs creep up and performance drifts downward with nobody noticing until audits reveal problems.
Procure transforms procurement from transactional to strategic.
It ingests purchase orders, invoices, vendor performance data, delivery records, quality metrics, contract terms, market pricing, and supplier information. It learns optimal vendor strategies, price trends, performance patterns, and negotiation leverage. It analyzes procurement spend and recommends optimization.
When you're purchasing commodities at prices 12% above market rates, Procure identifies suppliers offering better terms and recommends switching. When a vendor's on-time delivery has degraded from 98% to 91%, Procure flags performance decline and recommends corrective action. When supplier consolidation is creating single-point-of-failure risk, Procure identifies dual-sourcing opportunities. When contract renewal approaches, Procure recommends negotiation timing and leverage points based on market analysis.
Procurement organizations using Procure have reduced spend by 22% on average through optimized vendor selection and negotiation. On-time delivery improved 38% because supplier performance is monitored and underperformers are addressed. Supplier diversity improved because alternative suppliers are systematically evaluated instead of overlooked.
The interface shows procurement landscape clearly. Vendor performance metrics display on-time delivery, quality, pricing, and reliability. Spend analysis shows current vs. market rates. Cost reduction opportunities highlight savings potential by vendor and category. Negotiation recommendations appear with leverage analysis. Contract timeline alerts surface renewal opportunities. Supplier benchmarking shows competitive positioning.
Procure doesn't replace procurement professionals. It gives them data-driven insights so they negotiate strategically instead of accepting standard terms. They identify cost reductions and performance improvements systematically instead of relying on sporadic audits.
Integrated through Merak's Unified API, it connects to your procurement systems, vendor databases, market pricing sources, and contract repositories instantly. Every purchase and supplier interaction feeds continuous procurement intelligence.
Procure turns procurement from transactional to strategic. Costs decrease. Performance improves. Negotiation leverage increases. Supplier relationships strengthen through mutual performance visibility. Procurement becomes competitive advantage.""",
        "developer": "Momentum Procurement",
        "demo_link": DEMO_LINK_ID,
        "base_rate": 1399,
        "success_rate": 95,
        "experience_years": 6,
        "industry": "vendor management & procurement",
        "languages": ("English", "Spanish", "German", "French", "Mandarin", "Portuguese"),
        "endorsements": (
            {
                "endorser_name": "Tim Cook",
                "endorser_role": "Chief Executive Officer, Apple",
                "endorsement_text": (
                    "Procurement optimization at Apple's scale compounds into enormous impact. Procure identified vendor performance"
                    " issues and cost reduction opportunities. Procurement spend decreased 22%. Supplier diversity improved measurably."
                ),
            },
            {
                "endorser_name": "Andy Jassy",
                "endorser_role": "Chief Executive Officer, Amazon",
                "endorsement_text": (
                    "Amazon's vendor ecosystem is massive. Procure provided visibility into supplier performance and pricing. On-time"
                    " delivery improved 38%. Strategic negotiations yielded cost reductions and better terms across categories."
                ),
            },
            {
                "endorser_name": "Carla Harris",
                "endorser_role": "Vice Chair, Morgan Stanley",
                "endorsement_text": (
                    "Financial services procurement spans technology, consulting, and professional services. Procure identified consolidation"
                    " opportunities and renegotiation leverage. Spend decreased while performance improved dramatically."
                ),
            },
        ),
    },
)
__all__ = ["DEMO_LINK_ID", "_RAW_AGENT_DATA"]
