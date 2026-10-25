# 黄金研究 Skill

从宏观驱动走到价格确认：先核对标的和数据，再研究利率、美元与避险需求，最后用多周期结构检查观点是否站得住。

作者：[Serennity007](https://github.com/Serennity007) · [四类研究导航](https://github.com/Serennity007/market-research-skills) · [完整 Skill](SKILL.md) · MIT

## 能做什么

1. 确认 XAUUSD、COMEX GC 或上期所 AU，分别记录币种、重量单位、合约月和价格口径，不能直接拼接比较。
2. 研究中期背景：实际利率、美元、流动性与黄金需求。明确是数据事实还是机制解释；出现相关性变化时保留分歧。
3. 用 H4/H1/M30 或使用者指定周期拆分趋势、触发和确认。对收复关键位、突破失败、回踩分别提出失效条件，不能把 MA/MACD 当作独立胜率证明。
4. 黄金与白银分别核验。金银比必须先统一计量和时间，白银的工业需求会使两者不完全同步。
5. 输出有条件的基准/上行/下行情景，标明数据缺口；按原时点追加复盘，不用后来的价格改写原判断。

这是可单独使用的研究 Skill：指令、参考、示例和计算脚本都在本仓库内，不依赖其他三个项目。离线脚本使用 Python 3.10+ 标准库，无 API Key。

## 快速体验

```bash
git clone https://github.com/Serennity007/gold-research-skill.git
cd gold-research-skill
python scripts/analyze_structure.py --csv examples/bars.csv --instrument GOLD_SYNTHETIC --timeframe H4 --as-of 2024-01-09T00:00:00+00:00 --data-kind synthetic --support 100 --out output/structure.json

python -m unittest discover -s tests -v
```

输出保存在 `output/`。重复运行请换文件名；脚本拒绝覆盖输入和已有结果。

先看 [输入样例](examples/bars.csv)、[结构计算输出](examples/structure-output.json) 和 [数据约定](references/data-contract.md)。K 线例子是 2024 年时间标签的构造数据，统一使用虚构标的名；归档时间不代表 2024 年曾经做过此分析。末端收复支撑但均线方向仍有分歧，示范如何保留冲突证据。



## 作为 Skill 使用

把本仓库完整复制到使用工具支持的技能目录，保留文件夹名 `gold-research-skill`。例如 Codex 的用户技能目录为 `~/.codex/skills/gold-research-skill`；有图形界面或其他代理时按其技能目录约定安装。

```text
使用 $gold-research-skill，标的是……，截止时间是……，数据来自……。
请核查证据与时效，给出有条件的研究结论、失效条件及复盘检查点。
```

需要当前行情时，使用者提供带来源和时间的文件，或由其已授权的数据工具获取。此仓库不内置行情订阅、账户接入和自动下单。

## 证据与验证范围

计算测试覆盖时间截止、输入校验、指标/领域算术和命令行文件保护。`examples/` 全部是 **synthetic 模拟样例**，用于验证功能；没有宣称真实行情测试、纸面账户收益或实盘盈利。作者的历史观点与证据等级见 [方法说明](references/method.md)。

共同 K 线引擎从作者 [选股与量化技能合集](https://github.com/Serennity007/awesome-stock-quant-skills/tree/67156b0aa4860894a8cdbc66b797db535531fe59/my-skills/gold-cross-asset-research) 的已收盘数据分析器适配而来。各仓库随带自身代码与测试，互不需要联网导入。

[研究与复盘记录模板](references/report-template.md) · [官方来源](references/sources.md)

本地验证（2026-10-25）：**8 项测试通过**，Skill 入口通过结构校验。[从输出到研究结论的模拟记录](examples/research-note.md) 展示保留分歧和留空未知结果的写法。
