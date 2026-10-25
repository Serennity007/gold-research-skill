"""Offline bilingual reports; HTML escapes all supplied strings."""
from html import escape
from .validation import dumps, stamp

TEXT = {
    "en": {
        "title": "Futures research desk", "synthetic": "SYNTHETIC EXAMPLE — constructed observations and hypothetical account/rule inputs; no historical performance.",
        "scope": "Descriptive observations, evidence gaps and hypothetical capacity arithmetic. Source claims and file hashes do not authenticate market data. A stop is not a maximum-loss guarantee.",
        "quality": "Quality gates", "market": "Fixed-contract observations", "fundamentals": "Published fundamentals", "basis": "Comparable basis", "curve": "Dated spreads", "recipes": "Declared processing recipes", "risk": "Hypothetical capacity and stress", "domain": "Research questions and falsification", "sources": "Source declarations", "details": "Complete machine-readable calculation", "chart": "Available D1 closes — elapsed UTC time on horizontal axis", "pass": "Configured checks passed; completeness and predictive validity are not established.",
        "clock": "Publication, availability and retrieval are separate clocks. Later data are excluded, not backfilled.", "omitted": "Not supplied / not calculable", "label": "Observation", "value": "Value", "next": "Next evidence to check", "limits": "Interpretation limits", "quantity": "Calculated lots are an upper ceiling under the supplied assumptions, not an order suggestion.",
    },
    "zh-CN": {
        "title": "期货研究工作台", "synthetic": "构造样例——观测、账户和规则参数均为假设，不能作为历史业绩。",
        "scope": "本报告包含描述性观察、证据缺口和假设容量计算。来源声明和文件哈希不能认证市场数据；止损价不是最大亏损保证。",
        "quality": "质量检查", "market": "固定合约观察", "fundamentals": "已公布基本面", "basis": "可比基差", "curve": "明确交割日期的价差", "recipes": "声明的加工配方", "risk": "假设容量与压力情景", "domain": "研究问题与证伪条件", "sources": "来源声明", "details": "完整机器可读计算", "chart": "已可用日线收盘价——横轴为 UTC 实际时间间隔", "pass": "配置的检查已通过；不表示已证明数据完整或预测有效。",
        "clock": "公布、可用和取数是不同时间。晚于截止的数据会被排除，不回填进过去。", "omitted": "未提供／无法计算", "label": "观察项", "value": "数值", "next": "下一步核对证据", "limits": "解释边界", "quantity": "手数是给定假设下的容量上限，不是下单建议。",
    }
}

GAPS = {
    "calendar_not_validated": ("No session calendar: freshness uses elapsed hours, without holiday/night-session validation.", "未提供交易时段表：仅按经过小时检查，未核验节假日和夜盘归属。"),
    "calendar_out_of_coverage": ("Cutoff is outside the declared calendar coverage.", "截止时点超出声明的交易日历覆盖范围。"),
    "missing_latest_completed_session": ("The last fully completed trading date is missing; dependent risk/basis is blocked.", "缺少最近完整交易日的数据；相关风险／基差计算已阻断。"),
    "stale_bars": ("Last bar exceeds the supplied age limit.", "最新价格超过声明的时效上限。"),
    "insufficient_atr_history": ("ATR14 needs 15 available daily bars; no estimate substituted.", "ATR14 需要至少 15 根可用日线；未用估算替代。"),
    "nonpositive_return_denominator": ("Percentage change omitted for a nonpositive starting price.", "起始价格非正，未计算百分比变化。"),
    "insufficient_seasonal_history": ("Seasonal percentile requires at least three prior, distinct comparable years.", "季节分位至少需要三个可比的历史年份，且不包含当年。"),
    "no_visible_fundamentals": ("No fundamental observation was available by the cutoff.", "截止时点没有可用基本面观测。"),
    "fundamentals_not_supplied": ("Fundamentals were not supplied; price changes do not prove a supply/demand cause.", "未提供基本面；价格变化不能证明供需因果。"),
    "basis_stale_or_asynchronous": ("Basis blocked by stale, asynchronous or incomplete-session inputs.", "基差因陈旧、不同步或缺少完整交易日输入而阻断。"),
    "curve_unavailable": ("Curve needs at least two fresh, synchronized dated contracts.", "期限结构需要至少两个时效合格且同步的明确合约。"),
    "recipe_stale_or_asynchronous": ("Processing result blocked by stale or asynchronous component prices.", "加工结果因组成价格陈旧或不同步而阻断。"),
    "risk_calculation_blocked": ("Capacity is unavailable: supply effective specifications and resolve freshness gaps.", "容量计算不可用：需要有效合约规则并解决行情时效缺口。"),
    "source_claims_not_authenticated": ("Imported source declarations have not been authenticated.", "导入数据的来源声明未经认证。"),
    "historical_archive_claim_not_independently_verified": ("Historical availability relies on a declared archive; it has not been independently verified.", "历史可用性依赖声明的档案记录，未经独立核验。"),
}

ZH = dict(zip(
    "status calculated blocked not_requested not_supplied review_gaps configured_checks_passed product contract currency unit trade_date observed_at available_at close observations first_trade_date fixed_contract_change_pct atr14_simple previous_trade_date previous_volume open_interest_change metric value previous_observed_at change_from_previous_observation prior_season_samples prior_only_percentile spot_minus_future pct_of_future scope spot_observed_at near far near_minus_far delivery_day_gap simple_annualized_far_premium_pct name output_unit assumption spec_version spec_source lots_ceiling planned_loss_per_lot fees_at_stop_per_lot slippage_per_lot initial_margin_per_lot planned_loss_total initial_margin_total entry_minus_latest_quote stress_loss remaining_equity stress_margin margin_shortfall price reason risk_budget margin_budget user_cap previous_volume ceilings binding_constraints model source policy retrieved_at url archive_reference".split(),
    "状态 已计算 已阻断 未请求 未提供 有待核对的缺口 配置检查通过 品种 合约 币种 单位 交易日 观测时间 可用时间 收盘价 观测数 起始交易日 固定合约变化百分比 简单ATR14 前次交易日 前次成交量 持仓变化 指标 数值 前次观测时间 较前次观测变化 历史季节样本数 仅用往年样本的分位 现货减期货 占期货价格百分比 可比口径 现货观测时间 近月 远月 近月减远月 交割日间隔天数 远月升水简单年化百分比 名称 输出单位 假设 规则版本 规则来源 手数上限 每手计划亏损 每手止损情景费用 每手滑点 每手初始保证金 计划总亏损 初始总保证金 假设入场与最新价格差 压力亏损 剩余权益 压力保证金 保证金缺口 价格 原因 风险预算 保证金预算 用户手数上限 前次成交量 各项上限 约束项 模型 来源 策略 取数时间 链接 档案参考".split()))
ZH.update({"exactly_one_effective_spec_required": "需要且只能有一份生效规则", "spec_not_supplied": "未提供合约规则", "market_freshness_unresolved": "行情时效尚未确认", "stale_or_asynchronous_quotes": "报价过时或不同步", "insufficient_or_stale_or_asynchronous_curve": "曲线端点不足、过时或不同步", "single_unencumbered_position_no_netting": "单头寸、未占用权益、无保证金抵扣", "method": "检查方式", "latest_completed_trade_date": "最近完整交易日", "within_coverage": "处于声明覆盖范围内", "elapsed_clock": "经过小时", "explicit_sessions": "显式交易时段表", "retrieval_snapshot": "取数时快照", "archived_publication": "声明的历史发布档案", "synthetic": "构造数据"})


def report(result, bars, lang):
    t = TEXT[lang]
    cn = lang == "zh-CN"
    e = lambda x: escape(str(x), quote=True)
    label = lambda x: ZH.get(str(x), str(x).replace("_", " ")) if cn else str(x).replace("_", " ")
    def value(x):
        if x is None:
            return t["omitted"]
        if isinstance(x, (dict, list)):
            return dumps(x).strip()
        return label(x) if isinstance(x, str) and x in ZH else str(x)
    md, html = [], []
    def para(text):
        md.extend([escape(str(text)), ""]); html.append("<p>" + e(text) + "</p>")
    def heading(key):
        md.extend(["## " + t[key], ""]); html.append("<h2>" + e(t[key]) + "</h2>")
    def table(rows):
        md.extend([f'| {t["label"]} | {t["value"]} |', "|---|---|"])
        body = []
        for key, item in rows:
            a, b = label(key), value(item)
            safe = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace("|", "\\|").replace("\n", " ")
            md.append("| " + safe(a) + " | " + safe(b) + " |")
            body.append(f"<tr><th scope='row'>{e(a)}</th><td>{e(b)}</td></tr>")
        md.append(""); html.append("<div class='scroll'><table>"+"".join(body)+"</table></div>")
    title = result["domain"]["title"][lang] + " · " + t["title"]
    md.extend(["# " + title, ""])
    para(result["data_kind"] + " · " + result["as_of_utc"])
    if result["data_kind"] == "synthetic":
        para(t["synthetic"])
    para(t["scope"])
    heading("quality")
    notes = [GAPS[x][1 if cn else 0] for x in result["quality"]["gaps"]] or [t["pass"]]
    for note in notes:
        para(note)
    para(t["clock"])
    heading("market")
    table([(k,v) for k,v in result["market"].items() if k != "calendar"])
    calendar = result["market"]["calendar"]
    table(calendar.items())
    if bars:
        xs = [stamp(row["observed_at"]).timestamp() for row in bars]
        ys = [float(row["close"]) for row in bars]
        xspan, yspan = max(xs)-min(xs), max(ys)-min(ys)
        points = " ".join(f'{25+750*(x-min(xs))/(xspan or 1):.2f},{160-130*(y-min(ys))/(yspan or 1):.2f}' for x,y in zip(xs,ys))
        html.append(f"<figure><figcaption>{e(t['chart'])}</figcaption><svg viewBox='0 0 800 195' role='img' aria-label='{e(t['chart'])}'><title>{e(t['chart'])}</title><path d='M25 170H775' stroke='#8a9ab0'/><polyline points='{points}' fill='none' stroke='#167c75' stroke-width='3'/><text x='25' y='190' font-size='11'>{e(bars[0]['observed_at'])}</text><text x='775' y='190' text-anchor='end' font-size='11'>{e(bars[-1]['observed_at'])}</text></svg><small>{e(min(ys))} – {e(max(ys))} {e(result['market']['unit'])}</small></figure>")
    heading("fundamentals")
    for item in result["fundamentals"]:
        table(item.items())
    if not result["fundamentals"]:
        para(t["omitted"])
    for key in ("basis", "curve"):
        heading(key)
        table([(k,v) for k,v in result[key].items() if k not in ("spreads", "limitation")])
        for spread in result[key].get("spreads", []):
            table(spread.items())
        if key == "curve":
            para("简单年化不包含持有成本、融资、税费或换月执行，不能解释为套利收益。" if cn else "Simple annualization excludes carry, financing, tax and roll execution; it is not an arbitrage return.")
    heading("recipes")
    for recipe in result["recipes"]:
        table([(k,v) for k,v in recipe.items() if k != "terms"])
    if not result["recipes"]:
        para(t["omitted"])
    heading("risk")
    table([(k,v) for k,v in result["risk"].items() if k not in ("stress", "limitation")])
    for stress in result["risk"].get("stress", []):
        table(stress.items())
    para(t["quantity"])
    para("模型仅覆盖单一、无既有占用的假设头寸；不包含组合相关性、保证金抵扣、经纪商加收和逐日结算现金路径。跳空和保证金上调可能使亏损超过预算。" if cn else "The model covers one hypothetical position using unencumbered equity. It excludes portfolio correlation, margin offsets, broker add-ons and daily settlement cash paths. Gaps and margin increases can exceed the loss budget.")
    heading("domain")
    for question in result["domain"]["questions"][lang]:
        para(question)
    heading("next")
    for item in result["domain"]["next_checks"][lang]:
        para(item)
    heading("sources")
    for role, item in result["sources"].items():
        table([("source", role), *item.items()])
    detail = e(dumps(result))
    html.append(f"<details><summary>{e(t['details'])}</summary><pre>{detail}</pre></details>")
    md.extend(["[JSON](bundle.json) · [English](REPORT.en.html) · [中文](REPORT.zh-CN.html)", ""])
    page = f'''<!doctype html><html lang="{lang}"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'"><title>{e(title)}</title><style>
    :root{{color-scheme:light dark}}body{{font:16px/1.65 system-ui,sans-serif;margin:0;background:#f2f5fa;color:#172b41}}main{{max-width:1080px;margin:auto;padding:30px 22px}}h1{{font-size:clamp(25px,4vw,40px)}}h2{{margin-top:35px;border-top:2px solid #b9d7da;padding-top:18px}}a{{color:#096a79}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{text-align:left;vertical-align:top;padding:10px;border:1px solid #ced9e3;white-space:pre-wrap;overflow-wrap:anywhere}}th{{width:38%}}.scroll,pre{{overflow:auto}}pre{{max-height:520px;font-size:12px}}svg{{width:100%;height:auto}}figure{{margin:20px 0}}nav{{display:flex;gap:16px;flex-wrap:wrap}}@media(prefers-color-scheme:dark){{body{{background:#101c2c;color:#dce7f4}}table{{background:#16263b}}a{{color:#8adbd4}}th,td{{border-color:#3a4f64}}}}@media print{{body,table{{background:#fff;color:#111}}details{{display:none}}tr{{break-inside:avoid}}}}</style><main><nav><a href="REPORT.en.html">English</a><a href="REPORT.zh-CN.html">中文</a><a href="bundle.json">JSON</a><a href="REPORT.{lang}.md">Markdown</a></nav><h1>{e(title)}</h1>{''.join(html)}</main></html>'''
    return "\n".join(md), page
