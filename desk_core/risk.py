"""Decimal capacity arithmetic for a hypothetical, unencumbered single position.

Fees and margin are user-supplied effective schedules, never exchange defaults.
"""
from decimal import Decimal, ROUND_FLOOR
from .validation import dec, integer, stamp, require, visible


def capacity(request, specs, market, cutoff, provenance):
    if not request:
        return {"status": "not_requested"}
    matching = []
    for item in specs:
        require(item.get("version") and item.get("source"), "spec version and source required")
        # A rule's observed_at is its publication event; effective_at may be later.
        valid = visible(item, cutoff, provenance)
        start, end = stamp(item["effective_at"]), stamp(item["expires_at"])
        require(start < end, "spec effective interval must increase")
        if item["contract"] == market["contract"] and valid and start <= cutoff < end:
            matching.append(item)
    require(len({x["version"] for x in matching}) == len(matching), "duplicate spec version")
    if len(matching) != 1:
        return {"status": "blocked", "reason": "exactly_one_effective_spec_required"}
    spec = matching[0]
    require(spec["currency"] == market["currency"] == request["currency"], "risk currency mismatch")
    require(spec["price_unit"] == market["unit"], "risk price-unit mismatch")
    require(stamp(spec["last_trade_at"]) > cutoff, "contract has reached declared last trading time")
    multiplier, tick = dec(spec["multiplier"], positive=True), dec(spec["tick"], positive=True)
    rate = dec(spec["margin_rate"], positive=True)
    require(rate <= 1, "margin_rate must not exceed 1")
    side = request["side"]
    require(side in ("long", "short"), "side must be long or short")
    entry, stop = dec(request["entry"], positive=True), dec(request["stop"], positive=True)
    require(all(p % tick == 0 for p in (entry, stop)), "entry/stop must be tick aligned")
    require(stop < entry if side == "long" else stop > entry, "stop must be adverse to entry")
    require(request["close_kind"] in ("close", "close_today"), "explicit close fee category required")
    fees = spec["fees"]
    def fee(kind, price):
        return dec(fees[kind]["per_contract"], minimum=0) + price * multiplier * dec(fees[kind]["ad_valorem"], minimum=0)
    # Validate even unused close schedules so missing close-today fees cannot hide.
    for kind in ("open", "close", "close_today"):
        fee(kind, entry)
    slips = integer(request["slippage_ticks_per_side"])
    closing = request["close_kind"]
    fees_stop = fee("open", entry) + fee(closing, stop)
    slippage = 2 * slips * tick * multiplier
    planned_loss = abs(entry-stop) * multiplier + fees_stop + slippage
    margin = entry * multiplier * rate
    equity = dec(request["unencumbered_equity"], positive=True)
    risk_budget, margin_budget = dec(request["risk_budget"], minimum=0), dec(request["margin_budget"], minimum=0)
    require(risk_budget <= equity and margin_budget <= equity, "budgets exceed unencumbered equity")
    participation = dec(request["max_previous_volume_fraction"], minimum=0)
    require(participation <= 1, "volume fraction must be <=1")
    require(market.get("previous_volume") is not None, "previous observation volume needed for liquidity ceiling")
    floor = lambda x: int(x.to_integral_value(rounding=ROUND_FLOOR))
    ceilings = {"risk_budget": floor(risk_budget/planned_loss), "margin_budget": floor(margin_budget/margin),
                "user_cap": integer(request["max_lots"]), "previous_volume": floor(dec(market["previous_volume"]) * participation)}
    lots = min(ceilings.values())
    stresses = []
    for scenario in request.get("stress", []):
        adverse = dec(scenario["adverse_price_fraction"], minimum=0)
        require(adverse < 1, "adverse price fraction must be <1")
        stress_rate = dec(scenario["margin_rate"], positive=True)
        require(stress_rate <= 1, "stress margin rate must be <=1")
        price = entry * (1-adverse if side == "long" else 1+adverse)
        loss = (entry * adverse * multiplier + fee("open", entry) + fee(closing, price) + slippage) * lots
        remaining = equity-loss
        needed = price * multiplier * stress_rate * lots
        stresses.append({"name": str(scenario["name"]), "price": price, "stress_loss": loss,
                         "remaining_equity": remaining, "stress_margin": needed,
                         "margin_shortfall": max(Decimal(0), needed-remaining)})
    return {"status": "calculated", "spec_version": spec["version"], "spec_source": spec["source"],
            "currency": request["currency"], "lots_ceiling": lots, "ceilings": ceilings,
            "binding_constraints": [key for key, value in ceilings.items() if value == lots],
            "planned_loss_per_lot": planned_loss, "fees_at_stop_per_lot": fees_stop,
            "slippage_per_lot": slippage, "initial_margin_per_lot": margin,
            "planned_loss_total": planned_loss * lots, "initial_margin_total": margin * lots,
            "entry_minus_latest_quote": entry-dec(market["close"]), "stress": stresses,
            "model": "single_unencumbered_position_no_netting",
            "limitation": "Stop execution is not guaranteed; stress loss can exceed the risk budget. Broker add-ons, daily settlement cash flows and existing portfolio exposures require separate review."}
