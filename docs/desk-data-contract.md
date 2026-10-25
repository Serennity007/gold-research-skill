# Research desk input contract / 研究工作台输入约定

Python 3.10+; standard library only. The eight research profiles share the versioned `desk_core` component. Legacy sector/specialist commands remain available and retain their documented assumptions.

## Start with a reproducible example

```bash
python scripts/run_desk.py run --config examples/desk-demo/ferrous/config.json --out output --lang en
python scripts/run_desk.py verify output/desk-EXACT-RUN-DIRECTORY
python scripts/run_desk.py replay output/desk-EXACT-RUN-DIRECTORY --out output --lang zh-CN
```

Each run writes **both languages**: `REPORT.en.html`, `REPORT.zh-CN.html`, matching Markdown, a preferred-language `index.html` and `REPORT.md`, `bundle.json`, frozen raw inputs, a frozen configuration and a SHA-256 completion manifest. HTML has no network requests, external fonts or executable scripts. The price chart spaces observations by elapsed UTC time. JSON field names remain stable English identifiers; user-supplied metric names/units are preserved.

All examples are constructed observations with hypothetical rules and account settings. They are not retrieved market prices, a real exchange calendar, recommended sizing parameters or a strategy backtest. `_DEMO_` contracts do not exist on an exchange.

## Configuration

See the fully populated `examples/desk-demo/<profile>/config.json` rather than guessing field names.

| Field | Meaning |
|---|---|
| `schema_version` | Integer `1` |
| `profile` | `gold`, `crude-oil`, `ec-shipping`, `equity-index`, `ferrous`, `nonferrous`, `chemicals`, `agriculture` |
| `data_kind` | `synthetic` or `imported_observations`; never silently substituted |
| `as_of` | ISO-8601 timestamp with UTC offset |
| `instrument` | Explicit `product`, dated `contract`, ISO currency and `unit` |
| `files` | Required `bars`; optional `sessions`, `fundamentals`, `spot`, `curve`, `prices`, `spec` |
| `limits` | Explicit `quote_age_hours`, `quote_skew_minutes`, optional nonnegative integer `publication_grace_minutes` |
| `calendar_valid_until` | Required with sessions; explicit horizon of the supplied calendar |
| `basis` | With spot: selected `spot_id` and exact `scope` string |
| `curve_scope` | With curve: exact benchmark/quality/location/tax/delivery scope |
| `recipes` | Optional user-declared coefficient recipes; see below |
| `risk` | Optional hypothetical capacity request; see [capacity model](desk-risk-model.md) |

Paths must be portable relative files under the configuration directory: no absolute paths, `..`, drive prefixes, backslashes, symlinks or junctions. JSON rejects duplicate keys and nonfinite constants. CSV is UTF-8 (BOM permitted), with unique headers and exact row widths. A file is limited to 16 MiB and 100,000 CSV observations. Numeric fields reject booleans, nonfinite values and absolute magnitudes above 1e24. Times require explicit offsets. Values are computed using `Decimal` and serialized as decimal strings, avoiding binary floating-point rounding in capacity limits.

## Three clocks and historical revisions

Every time-varying observation requires `observed_at`, `published_at`, `available_at`, with:

```
observed_at <= published_at <= available_at <= as_of
```

Rows later than the cutoff are counted and excluded. Among visible versions of the same event, the latest publication/availability pair is selected. Duplicate versions with identical event and clocks are rejected, even if values happen to agree. Incorrect clocks or invalid values fail validation; a future row is not permission to smuggle malformed data into the input.

Imported inputs additionally need `sources.<role>.name`, `retrieved_at`, and one of:

- `policy: retrieval_snapshot`: retrieval must be no later than cutoff; row availability must be at least retrieval time. A download today cannot establish what was known yesterday.
- `policy: archived_publication`: provide `archive_reference`. Historical availability is a user-declared archive claim and produces a visible unverified-archive gap. A later retrieval can read the archive but cannot authenticate it.

The session calendar is a static declared schedule rather than a revised observation table. Effective rule schedules use the same provenance policy as other data. Source URLs and names are stored as text; no network retrieval or source authentication is performed by this command.

## CSV roles

All roles below except `sessions` require the three clocks above.

| Role | Required additional columns |
|---|---|
| `bars` | `product,contract,trade_date,open,high,low,close,volume,open_interest,currency,unit` |
| `fundamentals` | `metric,value,unit,season_key` |
| `spot` | `spot_id,price,currency,unit,scope` |
| `curve` | `product,scope,contract,delivery_date,price,currency,unit` |
| `prices` | `price_id,price,currency,unit` |
| `sessions` | `product,trade_date,start_time,end_time` |

`bars` is **daily only**. `observed_at` is the final session close of the provided trading date. It is not an intraday current-price slot. Open/high/low/close must form a valid bar; volume and open interest are nonnegative integers in contracts. Contract, product, unit and currency must match the declared instrument for every bar. Continuous/main-contract series are not accepted as silent dated-contract roll splices; split into separate studies and explain the roll.

With sessions, the final daily close is the maximum end time of **all** sessions assigned to a trading date. A Friday night session assigned to Monday does not complete Monday's daily bar. The cutoff plus declared publication grace determines the last fully completed trading date; a missing latest completed day blocks dependent basis/capacity. Overlapping sessions and a close that does not equal the final declared session are rejected. The calendar must cover the study bars. A cutoff outside its stated coverage produces a gap and blocks dependent calculations. These checks validate consistency with the supplied calendar, not its authenticity or completeness against an exchange.

Without sessions, freshness uses elapsed hours and the report explicitly says holidays/night sessions were not validated. A valid weekend/holiday calendar can keep Friday as the latest completed daily bar; spot/curve/recipe quote comparisons still use their explicit elapsed-age and synchronization thresholds.

Fundamentals use a metric identity that must already encode geography, grade, coverage and frequency when relevant. Units cannot change within a metric. Changes compare the latest two distinct observations, retaining both observation times: they are not automatically called daily/weekly/year-on-year changes. Seasonal percentile uses only earlier **distinct years** sharing the declared season key, requires at least three years, and uses `(less + 0.5*equal)/N*100`. The current year never enters its own reference distribution. Matching crop phases and leap/week conventions remains a declared research assumption. Values are not normalized or annualized automatically.

## Comparable arithmetic

- Basis = selected spot minus fixed-contract last daily close. Currency, unit and scope must match; both quotes must pass age and maximum skew. Scope should encode quality, location, tax and delivery terms or exact index definition. Index basis is descriptive; the tool does not turn index points into a deliverable spot asset.
- Curve uses latest visible quote per contract, explicit future delivery dates, matching product/currency/unit/scope, unique delivery dates and synchronized quotes. Adjacent spread = near minus far. Simple annualized far premium = `(far/near - 1) * 365 / delivery_day_gap * 100`, only when both prices are positive. It is a descriptive ratio, excluding carry, financing, taxes and execution. The program does not infer exchange expiry rules from symbols.
- Ordinary percentage price changes require a positive starting denominator. Crude-oil bars may be signed; a nonpositive denominator yields null and a gap rather than an invented return. Risk capacity's positive-price margin model cannot handle zero/negative entry prices.
- Recipes = sum(`quantity_per_output * price`) minus `fixed_cost_per_output`. Each term declares `price_id`, exact `input_unit`, signed coefficient and `quantity_unit`; the recipe declares currency, output basis and assumptions. Input currencies/units must match their declarations and quotes must be fresh/synchronized. **Coefficient dimensions, actual yields, taxes, co-products and coverage are supplied by the researcher, not inferred or certified by the engine.** These are declared processing spreads, not universal plant profits.

## Quality states and reproducibility

Malformed/contradictory input returns CLI exit 2 with JSON error text. Missing optional input stays `not_supplied`/`not_requested`. A calculable result can carry named evidence gaps; it is not a buy/sell signal. Dependent calculations block when their required freshness/rules cannot be established. `configured_checks_passed` means only the specified checks passed; it is not a probability, coverage score or prediction validation.

`COMPLETE.json` hashes every other file and checks the exact file set. Frozen-config loading verifies the bundle before reading inputs. Replay requires the identical core source/profile hashes and compares all computed fields except generation time and the raw configuration hash (paths change when frozen). An ordinary run against a verified old snapshot is a **new analysis**, not a reproducibility claim. SHA-256 proves local consistency against the supplied manifest; someone who can replace the manifest can replace the evidence. It is not a signature or proof of genuine historical publication.

## 中文操作要点

先复制对应 `examples/desk-demo/<profile>` 目录，再替换为自己的获授权数据。保留原始观测、公布时间与实际可用时间，填写明确合约、币种、单位、来源和时效阈值；不要把今天取到的修订数据回填为过去已知信息。

夜盘按提供的交易日处理，不根据自然日期猜测。日线必须等该交易日所有时段结束；缺失最近完整交易日会阻断依赖计算。基差和加工配方必须先对齐口径、时间及单位。仓单、交易所库存、社会库存之间先核对包含关系，不直接相加。

同一次运行始终生成中英双语报告；`--lang zh-CN` 仅指定默认首页语言。原始数据字段和 JSON 标识保持原样，避免翻译改变研究口径。哈希校验只证明相对于清单的文件一致性，不能认证来源或证明历史上当时能获得这份数据。
