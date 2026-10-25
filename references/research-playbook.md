# Gold / 黄金

Use the user's requested instrument, window and language. Do not invent a current contract, data subscription, margin schedule or market observation.

## Evidence to establish before interpretation

Record the dated contract, exchange, quote unit/currency, relevant delivery or index definition, cutoff with offset, observation/publication/availability times, and original source. On a roll, keep both contracts and their overlap explicit; do not splice the move into a return.

## Chain-specific hypotheses and failure conditions

- Separate USD gold, CNY gold and FX conversion before attributing a domestic move. Match quote times, mass units, fineness and tax/delivery scope.
- A real-yield or dollar move is an explanatory hypothesis, not a deterministic gold signal. Align publication clocks and state the observation window.
- A gold/silver ratio requires synchronized currencies and mass units. Ratio extremes alone do not demonstrate mean reversion.
- Distinguish physical premium, exchange inventory, ETF holdings and central-bank announcements; their frequencies, revisions and coverage differ.
- Falsify a shortage explanation if physical premia and deliverable supply fail to confirm it; keep geopolitical narratives separate from observed flows.

## Representative evidence series

- `real_yield_pct`: declare source coverage, native units, publication cadence and revision policy before comparing values.
- `physical_premium`: declare source coverage, native units, publication cadence and revision policy before comparing values.
- `inventory`: declare source coverage, native units, publication cadence and revision policy before comparing values.

A missing series is a gap, not zero. Explain which claim it would support or contradict. Use `fundamentals.metric` names that distinguish region, grade and coverage; the engine does not infer these from a short label.

## Practical research delivery

1. Preserve the supplied files and source claims; state whether the evidence is synthetic, retrieved now or an archived vintage.
2. Run `scripts/run_desk.py` for daily observations, vintages, comparable basis/curve, declared processing recipes and hypothetical capacity. Use existing specialist commands where their native macro, breadth, route or curve inputs fit better.
3. Read the quality gates before interpreting numbers. Reject unit/identity contradictions. Describe unavailable calculations rather than hiding them.
4. Write the observed facts first, then the proposed transmission mechanism, the strongest contrary evidence, and the next publication/event that can falsify it. Cite the original source for substantive imported claims.
5. If the user requests a setup, retain their declared trigger, confirmation, invalidation and time limit; do not manufacture historical signals after seeing future data. Separate a scenario from a forecast.
6. If capacity is requested, require the user's budget and effective rule schedule; report stress beyond the stop plan and the model's single-position scope. Do not select risk parameters for the user.

## Next checks

- Check official rate/FX releases and the same observation window.
- Reconcile premium, warehouse and holdings evidence without double counting.
- Recheck the effective contract and broker margin/fee notices before capacity arithmetic.

## 中文研究要点

- 先区分美元金价、人民币金价与汇率折算，再归因国内变化。报价时点、质量单位、成色及税费交割口径必须一致。
- 实际利率与美元变化只是解释假设，不是确定的黄金信号；对齐公布时间并写清观察窗口。
- 金银比需要同步币种与质量单位；比值极端不能单独证明均值回归。
- 实物升水、交易所库存、ETF持仓与央行公告的频率、修订和覆盖不同，分别记录。
- 实物升水与可交割供应不确认时，应降低短缺解释的置信度；地缘叙事与实际流量分开。

- 核对官方利率／汇率发布与相同观察窗口。
- 交叉核对升水、仓储和持仓证据，避免重复计数。
- 容量计算前重新核对有效合约规则和经纪商保证金、费用通知。

## Review exercises

- A user supplies a continuous contract and asks for a roll-period return: obtain dated contracts/overlap or label the result unavailable; do not reinterpret the continuous code as a deliverable contract.
- An inventory revision was published after the report cutoff: exclude that vintage and retain the previously available observation; show the exclusion count.
- A large calculated premium has asynchronous quotes or different tax/quality scope: block the comparison and identify the precise input needed.
- A user asks for the 'best trade' with no current data: supply conditional research questions and evidence gaps; do not invent a current market or implied confidence score.
- A simulated loss budget fits twelve lots but an adverse gap exceeds it: report both values and state why the stop cannot guarantee that budget.
