# Evidence and rule maintenance / 证据与规则维护

Research observations, source claims and interpretation have different assurance levels. Preserve original provider files, publication identifiers, retrieval timestamps and any revision metadata. If only a present-day download exists, mark it `retrieval_snapshot`; do not claim first-vintage availability. `archived_publication` requires an archive reference and remains explicitly unverified by this tool.

Use primary publications for rule claims. The following official materials establish the kinds of distinctions the desk preserves; they are **reference entry points, not a live parameter feed**:

- [SHFE settlement rules, published June 2026](https://www.shfe.cn/regulation/exchangerules/rules/202606/t20260603_831935.html): daily settlement involves more than the initial margin estimate. Check the currently applicable rule and amendments for the contract and account.
- [INE EC standard contract](https://www.ine.com.cn/products/futures/index_f/ec_f/standard_ec_f/202602/t20260210_830423.html) and [INE delivery rules, June 2026](https://www.shfe.cn/regulation/ineregulation/businessmethods/delivery/202606/t20260626_832297.html): settlement-index futures require the specified index and settlement observation rules. A booking quote is not a replacement for that index.
- [SHFE warehouse warrant guide](https://www.shfe.cn/services/delivery/warehousewarrant1/): a warrant is a delivery document with eligibility and workflow conditions; it is not a synonym for every warehouse's total physical stock.
- [CFFEX settlement rules PDF](https://www.cffex.com.cn/u/cms/www/202003/27161736r3ck.pdf): consult the applicable revision for index settlement. The URL path alone does not establish a document's effective date.

The desk does not ship any of these as current numerical fees/margins. For SHFE, INE, DCE, CZCE, GFEX or CFFEX instruments, obtain the **effective contract-specific** spec, last-trading schedule, exchange notice and broker schedule before importing `spec.json`. Save the notice ID/URL and source version. The provided calendars are synthetic and must be replaced with the relevant exchange sessions and holiday adjustments.

For a substantive research statement, keep an evidence ledger with: claim; observed period; publication/available time; exact series/unit/coverage; original source; contrary evidence; uncertainty; next check. When a link cannot be retrieved, retain the failure and label the claim unverified. Do not substitute secondary commentary as if it were the original announcement.

## 中文研究纪律

将观察事实、解释假设和需要补充的证据分开写。用原始公告或统计发布支持规则与数据口径；记录公布时点、实际可用时点、取数时间、版本和相反证据。官方入口也可能更新，实际手续费、平今、保证金、限仓、交割资格和最后交易日必须按当次合约及账户重新核实。

本工具不会联网下单，不保存 API 密钥，不自动登录数据终端，不扫描第三方系统。用户导入自己有权使用的数据；没有观测时输出缺口，不能用构造数据替代真实行情后宣称分析成功。
