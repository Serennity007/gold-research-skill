---
name: gold-research-skill
description: 分析黄金的多周期价格结构、利率和美元背景、黄金白银联动及研究复盘。用于黄金研究与观点核验，不用于个股筛选或自动交易。
license: MIT
metadata:
  author: Serennity007
  version: "1.1.0"
---

# 黄金研究 Skill

从宏观驱动走到价格确认：先核对标的和数据，再研究利率、美元与避险需求，最后用多周期结构检查观点是否站得住。

## 工作方式

1. 确认 XAUUSD、COMEX GC 或上期所 AU，分别记录币种、重量单位、合约月和价格口径，不能直接拼接比较。
2. 研究中期背景：实际利率、美元、流动性与黄金需求。明确是数据事实还是机制解释；出现相关性变化时保留分歧。
3. 用 H4/H1/M30 或使用者指定周期拆分趋势、触发和确认。对收复关键位、突破失败、回踩分别提出失效条件，不能把 MA/MACD 当作独立胜率证明。
4. 黄金与白银分别核验。金银比必须先统一计量和时间，白银的工业需求会使两者不完全同步。
5. 输出有条件的基准/上行/下行情景，标明数据缺口；按原时点追加复盘，不用后来的价格改写原判断。

## 按任务读取

- 解释驱动、拆解情景或审核观点时，读 [研究方法](references/method.md)。
- 导入数据或解释指标时，读 [文件与时间契约](references/data-contract.md)。
- 写研究报告和复盘时，读 [记录字段](references/report-template.md)。
- 核查外部口径时，使用 [官方来源入口](references/sources.md)，记录实际访问日期。

## 研究工作台

完整研究时先读 [工作台与高级数据](references/workbench.md)。使用者给了数据就核对来源、口径和截止时间，运行本地报告；只有问题没有当前数据时，给缺口清单和情景框架。

```bash
python scripts/run_research.py --config examples/workbench.json --out output
```

报告同时输出 HTML、Markdown、JSON，冻结输入并提供可重跑配置。保留陈旧数据、证据冲突、样本缺失和未就绪指标；不把工具生成的报告视为人工核验结论。若讨论当日计划，区分观察条件、确认条件、失效条件和下次检查事件；复盘追加记录，不改写原计划。

## 单项离线计算

在仓库根目录运行；其他目录运行时将脚本、输入和输出替换成对应绝对路径。

```bash
python scripts/analyze_structure.py --csv examples/bars.csv --instrument GOLD_SYNTHETIC --timeframe H4 --as-of 2024-01-09T00:00:00+00:00 --data-kind synthetic --support 100 --out output/structure.json
```

附带数据全部为构造样例。更换真实数据后使用 `--data-kind imported_observations` 并填写来源，不因为标签变化而宣称实测收益。未提供当前数据时可以给研究框架和明确缺口，不能编造即时行情。

保留当时可知信息；未公布数据、未来 K 线不能进入历史结论。工具只做描述计算，不提供已验证的胜率、收益或自动执行。
