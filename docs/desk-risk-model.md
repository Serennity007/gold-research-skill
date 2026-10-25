# Hypothetical capacity and stress / 假设容量与压力模型

This calculator answers a narrow question: under **explicit user inputs**, what whole-lot ceiling satisfies each declared budget for one new position using unencumbered equity? It does not choose a direction, entry, stop, risk budget or participation threshold.

## Versioned specifications

`files.spec` is a JSON array of rule schedules. Each needs:

- `version`, `source`, exact `contract`, `currency`, `price_unit`;
- `observed_at`, `published_at`, `available_at`;
- `effective_at` inclusive, `expires_at` exclusive, `last_trade_at`;
- positive `multiplier`, `tick`, `margin_rate` (at most 1);
- `fees.open`, `fees.close`, `fees.close_today`, each declaring nonnegative `per_contract` and `ad_valorem` components.

Exactly one visible, effective schedule must apply to the declared contract. Overlapping schedules block the result; explicitly end the old schedule before the new one starts. Do not invent a fee of zero because a close-today category is unknown. Every fee category is required, even if not selected for this calculation. Fees are additive components: enter zero explicitly when the actual schedule has only one component. Round-lot calculation uses the declared broker margin, not a presumed exchange minimum. The example schedule is **fictional** and intentionally does not mirror a live contract's multiplier, tick, fees or margin.

## Request and formulas

See `risk` in the example configuration. `entry` and adverse `stop` must be positive, aligned to tick, and match the spec currency/price unit. A long stop must be below entry, a short stop above. Both budgets must be no greater than `unencumbered_equity`. Select `close` or `close_today` explicitly.

```
fee(kind, price) = per_contract[kind] + price * multiplier * ad_valorem[kind]
round_trip_slippage = 2 * slippage_ticks_per_side * tick * multiplier
planned_loss_per_lot = abs(entry-stop) * multiplier
                    + fee(open,entry) + fee(close_kind,stop) + round_trip_slippage
initial_margin_per_lot = entry * multiplier * margin_rate

lots = min(
  floor(risk_budget / planned_loss_per_lot),
  floor(margin_budget / initial_margin_per_lot),
  user_max_lots,
  floor(previous_observation_volume * max_previous_volume_fraction)
)
```

The previous volume is from the previous actual available daily observation; its trading date is retained. The participation limit is an illustrative daily-liquidity ceiling, **not** a fill model. It does not account for intraday liquidity, order-book depth, market impact, price limits or exchange position limits. A nonzero result does not establish that a trade can be executed. Entry may differ from the latest quote; that difference is shown explicitly, without assuming the entry filled.

All capacity comparisons use decimal arithmetic before flooring. No hidden rounding up is applied. A budget just below one lot's calculated loss produces zero lots. Fee rounding/minimums must be reflected in the declared schedule; the model does not infer broker-specific rounding rules.

## Stress is separate from the stop plan

For each user-declared adverse price fraction `g` and new margin rate:

```
stress_price = entry * (1-g) for long, entry * (1+g) for short
stress_loss = lots * (entry*g*multiplier + fees_at_stress_price + slippage)
remaining_equity = unencumbered_equity - stress_loss
stress_margin = lots * stress_price * multiplier * new_margin_rate
margin_shortfall = max(0, stress_margin - remaining_equity)
```

These are hypothetical end states, with closure fees reserved conservatively while also showing the margin requirement if the position remains open. They do not simulate cash movements between daily settlement events, forced liquidation priority, collateral haircuts or a complete broker account. The stress fraction is restricted below 1 for this positive-price model. A stress loss can exceed the planned risk budget; a stop cannot cap gap, limit-locked or unfilled losses. The result covers one position only: existing positions, correlated positions, hedges, margin offsets and portfolio aggregation require another model.

## Hand calculation used in tests

Entry 100, long stop 95, multiplier 10, tick 1, two one-tick slippages; open fee 2 + 0.0001 notional, close-today fee 5 + 0.0001 notional:

- Fees: `2 + 0.1 + 5 + 0.095 = 7.195`.
- Slippage: `2 * 1 * 1 * 10 = 20`.
- Planned loss: `50 + 7.195 + 20 = 77.195` per lot.
- Risk budget 1000 permits 12 lots; loss total `926.340`.
- At 10% margin, each lot uses 100 margin. The final ceiling also checks the other three limits.
- With `77.194999999999999999` risk budget, the ceiling is zero; with `77.195`, it is one, if other limits allow it.
- An 8% adverse gap at 12 lots exceeds the 1000 plan budget. This is expected behavior, not a passed loss guarantee.

## 中文解释

这是给定入场、止损、账户、费用和规则后的单头寸容量上限计算，不负责推荐这些参数。缺少有效规则、行情过时或最新完整交易日缺失时会阻断。开仓、平仓、平今费用分别填写；保证金应包含实际经纪商要求，不能把交易所最低标准当成账户实际占用。

计划亏损包含价差、双边费用和双边滑点；整手数向下取整并同时受风险预算、保证金预算、用户上限及前次成交量限制。跳空、涨跌停和无法成交会突破止损计划。压力情景单独显示剩余权益、保证金需求和缺口，不把止损金额写成最大可能损失，也不声称已覆盖组合风险。
