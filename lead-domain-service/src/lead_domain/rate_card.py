"""The agency rate card: the one formula used to price every Private Car
quote. Only this rate card is used — no external rating service is called.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from lead_domain.models import CoverageType


def round_to_nearest_rupee(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def rate_risk(
    *,
    coverage_type: CoverageType,
    idv: Decimal,
    no_claim_bonus_fraction: Decimal,
    loading_percent: Decimal,
    third_party_base_premium: Decimal,
    own_damage_rate: Decimal,
) -> dict[str, Decimal]:
    """Apply the agency rate card formula for the given coverage type.

    Comprehensive: own damage = IDV * own_damage_rate * (1 - no_claim_bonus_fraction).
    Third Party coverage carries no own-damage component (no vehicle damage cover).
    Loading is applied as a percentage of the pre-loading premium (own damage +
    third party) for both coverage types. The total is rounded to the nearest
    rupee.
    """

    if coverage_type == CoverageType.COMPREHENSIVE:
        own_damage_premium = idv * own_damage_rate * (Decimal("1") - no_claim_bonus_fraction)
    else:
        own_damage_premium = Decimal("0")

    no_claim_bonus_amount = idv * own_damage_rate * no_claim_bonus_fraction
    if coverage_type != CoverageType.COMPREHENSIVE:
        no_claim_bonus_amount = Decimal("0")

    pre_loading_total = own_damage_premium + third_party_base_premium
    loading_amount = pre_loading_total * (loading_percent / Decimal("100"))
    total = pre_loading_total + loading_amount

    return {
        "own_damage_premium": own_damage_premium.quantize(Decimal("0.01")),
        "third_party_premium": third_party_base_premium.quantize(Decimal("0.01")),
        "no_claim_bonus_amount": no_claim_bonus_amount.quantize(Decimal("0.01")),
        "loading_amount": loading_amount.quantize(Decimal("0.01")),
        "total_premium": round_to_nearest_rupee(total),
    }
