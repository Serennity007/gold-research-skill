"""As-of observations, contract identity, comparable arithmetic and explicit gaps."""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from . import VERSION
from .validation import (require, stamp, day, dec, integer, csv_rows, read_json,
                         vintages, source)
from .risk import capacity

CLOCKS = ["observed_at", "published_at", "available_at"]
ROLES = {"bars", "fundamentals", "spot", "curve", "prices", "sessions", "spec"}


def analyze(config, raw, profiles):
    require(type(config.get("schema_version")) is int and config["schema_version"] == 1, "unsupported schema_version")
    require(config.get("data_kind") in ("synthetic", "imported_observations"), "explicit data_kind required")
    require(config.get("profile") in profiles, "unknown research profile")
    require("bars" in raw and set(raw) <= ROLES, "bars required; unknown input role")
    cutoff = stamp(config["as_of"])
    identity = config["instrument"]
    for key in ("product", "contract", "currency", "unit"):
        require(isinstance(identity.get(key), str) and bool(identity[key].strip()), "instrument identity required: " + key)
    require(len(identity["currency"]) == 3 and identity["currency"].isupper(), "ISO currency code required")
    limits = config["limits"]
    max_age = dec(limits["quote_age_hours"], positive=True)
    max_skew = dec(limits["quote_skew_minutes"], minimum=0)
    provenance = {role: source(config, role, cutoff) for role in raw}
    gaps, excluded = [], {}
    def gap(code):
        if code not in gaps:
            gaps.append(code)
    def selected(role, columns, event):
        rows = csv_rows(raw[role], [*columns, *CLOCKS])
        chosen, count = vintages(rows, event, cutoff, provenance[role])
        excluded[role] = count
        return rows, chosen
    def fresh(row):
        return Decimal(str((cutoff-stamp(row["observed_at"])).total_seconds())) <= max_age * 3600
    def comparable(rows):
        return all(fresh(row) for row in rows) and (
            max(stamp(x["observed_at"]) for x in rows)-min(stamp(x["observed_at"]) for x in rows)
        ).total_seconds() <= float(max_skew * 60)
    allbars, bars = selected("bars", ["product", "contract", "trade_date", "open", "high", "low", "close", "volume", "open_interest", "currency", "unit"], ["contract", "observed_at"])
    signed = profiles[config["profile"]].get("allow_signed_prices", False)
    for row in allbars:
        require(all(row[k] == identity[k] for k in ("product", "contract", "currency", "unit")), "bar contract/product/currency/unit mismatch; split rolls explicitly")
        day(row["trade_date"])
        o, h, l, c = (dec(row[k], positive=not signed) for k in ("open", "high", "low", "close"))
        require(l <= min(o, c) <= max(o, c) <= h, "inconsistent OHLC")
        integer(row["volume"]); integer(row["open_interest"])
    bars.sort(key=lambda x: stamp(x["observed_at"]))
    require(bool(bars), "no bars available as of cutoff")
    require(len({row["trade_date"] for row in bars}) == len(bars), "multiple D1 observations for one trading date")
    require([row["trade_date"] for row in bars] == sorted(row["trade_date"] for row in bars), "trading dates move backwards")
    last = bars[-1]
    calendar = {"method": "elapsed_clock", "latest_completed_trade_date": None}
    if "sessions" in raw:
        sessions = csv_rows(raw["sessions"], ["product", "trade_date", "start_time", "end_time"])
        end_by_day, intervals = {}, []
        for row in sessions:
            require(row["product"] == identity["product"], "session product mismatch")
            day(row["trade_date"])
            start, end = stamp(row["start_time"]), stamp(row["end_time"])
            require(start < end, "session start must precede end")
            intervals.append((start, end))
            end_by_day[row["trade_date"]] = max(end, end_by_day.get(row["trade_date"], end))
        intervals.sort()
        require(all(intervals[i-1][1] <= intervals[i][0] for i in range(1, len(intervals))), "overlapping sessions")
        horizon = stamp(config["calendar_valid_until"])
        require(horizon >= max(end_by_day.values()), "calendar horizon precedes listed sessions")
        known = min(x[0] for x in intervals) <= cutoff <= horizon
        if not known:
            gap("calendar_out_of_coverage")
        for row in bars:
            require(row["trade_date"] in end_by_day and stamp(row["observed_at"]) == end_by_day[row["trade_date"]], "D1 close must match final declared session, including night-session trading date")
        grace = integer(limits.get("publication_grace_minutes", 0))
        completed = [date for date, end in end_by_day.items() if end + timedelta(minutes=grace) <= cutoff]
        expected = max(completed) if completed else None
        calendar = {"method": "explicit_sessions", "latest_completed_trade_date": expected, "within_coverage": known}
        if expected is None or last["trade_date"] != expected:
            gap("missing_latest_completed_session")
    else:
        gap("calendar_not_validated")
        if not fresh(last):
            gap("stale_bars")
    closes = [dec(row["close"]) for row in bars]
    first = closes[0]
    tr = [max(dec(bars[i]["high"])-dec(bars[i]["low"]), abs(dec(bars[i]["high"])-closes[i-1]), abs(dec(bars[i]["low"])-closes[i-1])) for i in range(1, len(bars))]
    if len(tr) < 14:
        gap("insufficient_atr_history")
    if first <= 0:
        gap("nonpositive_return_denominator")
    market = {**identity, "trade_date": last["trade_date"], "observed_at": last["observed_at"],
              "available_at": last["available_at"], "close": closes[-1], "observations": len(bars),
              "first_trade_date": bars[0]["trade_date"], "fixed_contract_change_pct": (closes[-1]/first-1)*100 if first > 0 else None,
              "atr14_simple": sum(tr[-14:])/14 if len(tr) >= 14 else None,
              "previous_trade_date": bars[-2]["trade_date"] if len(bars)>1 else None,
              "previous_volume": integer(bars[-2]["volume"]) if len(bars)>1 else None,
              "open_interest_change": integer(last["open_interest"])-integer(bars[-2]["open_interest"]) if len(bars)>1 else None,
              "calendar": calendar}
    fundamentals = []
    if "fundamentals" in raw:
        every, chosen = selected("fundamentals", ["metric", "value", "unit", "season_key"], ["metric", "observed_at"])
        units = defaultdict(set)
        for row in every:
            dec(row["value"])
            require(bool(row["metric"].strip()) and bool(row["unit"].strip()), "fundamental metric/unit required")
            units[row["metric"]].add(row["unit"])
        require(all(len(x) == 1 for x in units.values()), "mixed units within fundamental metric")
        grouped = defaultdict(list)
        for row in chosen:
            grouped[row["metric"]].append(row)
        for name, rows in sorted(grouped.items()):
            rows.sort(key=lambda x: stamp(x["observed_at"]))
            current = rows[-1]
            current_year = stamp(current["observed_at"]).year
            prior = [x for x in rows[:-1] if current["season_key"] and x["season_key"] == current["season_key"] and stamp(x["observed_at"]).year < current_year]
            years = [stamp(x["observed_at"]).year for x in prior]
            require(len(years) == len(set(years)), "season_key must identify one observation per year and metric")
            values = [dec(row["value"]) for row in prior]
            value = dec(current["value"])
            percentile = (sum(v < value for v in values) + Decimal("0.5")*sum(v == value for v in values))/len(values)*100 if len(values)>=3 else None
            if percentile is None:
                gap("insufficient_seasonal_history")
            fundamentals.append({"metric": name, "value": value, "unit": current["unit"],
                                 "observed_at": current["observed_at"], "available_at": current["available_at"],
                                 "previous_observed_at": rows[-2]["observed_at"] if len(rows)>1 else None,
                                 "change_from_previous_observation": value-dec(rows[-2]["value"]) if len(rows)>1 else None,
                                 "prior_season_samples": len(prior), "prior_only_percentile": percentile})
        if not fundamentals:
            gap("no_visible_fundamentals")
    else:
        gap("fundamentals_not_supplied")
    basis = {"status": "not_supplied"}
    if "spot" in raw:
        every, chosen = selected("spot", ["spot_id", "price", "currency", "unit", "scope"], ["spot_id", "observed_at"])
        for row in every:
            dec(row["price"])
        targets = [x for x in chosen if x["spot_id"] == config["basis"]["spot_id"]]
        require(bool(targets), "requested spot observation unavailable")
        spot = max(targets, key=lambda x: stamp(x["observed_at"]))
        require(all(spot[k] == identity[k] for k in ("currency", "unit")), "basis currency/unit mismatch; provide explicit conversion upstream")
        require(spot["scope"] == config["basis"]["scope"] and bool(spot["scope"].strip()), "basis grade/location/tax/delivery scope mismatch")
        if comparable([last, spot]) and not any(x in gaps for x in ("missing_latest_completed_session", "calendar_out_of_coverage", "stale_bars")):
            delta = dec(spot["price"])-closes[-1]
            basis = {"status": "calculated", "spot_minus_future": delta,
                     "pct_of_future": delta/closes[-1]*100 if closes[-1]>0 else None,
                     "scope": spot["scope"], "spot_observed_at": spot["observed_at"], "contract": identity["contract"]}
        else:
            basis = {"status": "blocked", "reason": "stale_or_asynchronous_quotes"}
            gap("basis_stale_or_asynchronous")
    curve = {"status": "not_supplied"}
    if "curve" in raw:
        every, chosen = selected("curve", ["product", "scope", "contract", "delivery_date", "price", "currency", "unit"], ["contract", "observed_at"])
        for row in every:
            dec(row["price"])
            day(row["delivery_date"])
            require(row["currency"] == identity["currency"] and row["unit"] == identity["unit"], "curve currency/unit mismatch")
            require(row["product"] == identity["product"] and row["scope"] == config["curve_scope"] and bool(row["scope"].strip()), "curve product/benchmark/delivery scope mismatch")
        latest = {}
        for row in sorted(chosen, key=lambda x: stamp(x["observed_at"])):
            latest[row["contract"]] = row
        rows = sorted(latest.values(), key=lambda x: day(x["delivery_date"]))
        require(len({x["delivery_date"] for x in rows}) == len(rows), "duplicate curve delivery dates")
        require(all(day(x["delivery_date"]) > cutoff.date() for x in rows), "curve contains expired delivery date")
        if len(rows) < 2 or not comparable(rows):
            curve = {"status": "blocked", "reason": "insufficient_or_stale_or_asynchronous_curve"}
            gap("curve_unavailable")
        else:
            spreads = []
            for near, far in zip(rows, rows[1:]):
                p, q = dec(near["price"]), dec(far["price"])
                days = (day(far["delivery_date"])-day(near["delivery_date"])).days
                spreads.append({"near": near["contract"], "far": far["contract"], "near_minus_far": p-q,
                                "delivery_day_gap": days, "simple_annualized_far_premium_pct": (q/p-1)*365/days*100 if p>0 and q>0 else None})
            curve = {"status": "calculated", "spreads": spreads,
                     "limitation": "Delivery dates are explicit inputs; ratio excludes carry, financing, taxes and roll execution. It is not an arbitrage return."}
    recipes = []
    if config.get("recipes"):
        require("prices" in raw, "recipes require prices input")
        every, chosen = selected("prices", ["price_id", "price", "currency", "unit"], ["price_id", "observed_at"])
        for row in every:
            dec(row["price"])
        prices = {}
        for row in sorted(chosen, key=lambda x: stamp(x["observed_at"])):
            prices[row["price_id"]] = row
        require(len({x["name"] for x in config["recipes"]}) == len(config["recipes"]), "duplicate recipe name")
        for recipe in config["recipes"]:
            require(recipe.get("assumption") and recipe.get("output_unit") and bool(recipe.get("terms")), "recipe assumptions/terms/output_unit required")
            used, total = [], -dec(recipe["fixed_cost_per_output"], minimum=0)
            for term in recipe["terms"]:
                require(term.get("quantity_unit") and term.get("price_id") in prices, "recipe quantity unit or visible price missing")
                row = prices[term["price_id"]]
                require(row["currency"] == recipe["currency"] and row["unit"] == term["input_unit"], "recipe currency/unit mismatch")
                total += dec(term["quantity_per_output"]) * dec(row["price"])
                used.append(row)
            valid = comparable(used)
            recipes.append({"name": recipe["name"], "status": "calculated" if valid else "blocked",
                            "value": total if valid else None, "currency": recipe["currency"],
                            "output_unit": recipe["output_unit"], "assumption": recipe["assumption"],
                            "terms": recipe["terms"], "fixed_cost_per_output": recipe["fixed_cost_per_output"]})
            if not valid:
                gap("recipe_stale_or_asynchronous")
    risk = {"status": "not_requested"}
    if config.get("risk"):
        if "spec" not in raw:
            risk = {"status": "blocked", "reason": "spec_not_supplied"}
        elif any(x in gaps for x in ("stale_bars", "missing_latest_completed_session", "calendar_out_of_coverage")):
            risk = {"status": "blocked", "reason": "market_freshness_unresolved"}
        else:
            specs = read_json(raw["spec"])
            require(isinstance(specs, list), "spec file must be a JSON array")
            risk = capacity(config["risk"], specs, market, cutoff, provenance["spec"])
        if risk["status"] == "blocked":
            gap("risk_calculation_blocked")
    if config["data_kind"] == "imported_observations":
        gap("source_claims_not_authenticated")
        if any(x["policy"] == "archived_publication" for x in provenance.values()):
            gap("historical_archive_claim_not_independently_verified")
    return {"schema_version": 1, "engine_version": VERSION, "profile": config["profile"],
            "data_kind": config["data_kind"], "as_of_utc": cutoff.isoformat(), "market": market,
            "fundamentals": fundamentals, "basis": basis, "curve": curve, "recipes": recipes,
            "risk": risk, "quality": {"status": "review_gaps" if gaps else "configured_checks_passed",
                                       "gaps": gaps, "excluded_future_vintages": excluded},
            "sources": provenance, "domain": {key: profiles[config["profile"]][key] for key in ("title", "questions", "next_checks", "metrics")},
            "scope": "Descriptive research and hypothetical capacity arithmetic. No orders, prediction validation, source authentication or portfolio risk aggregation."}
