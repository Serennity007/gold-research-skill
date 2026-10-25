# 研究工作台与高级数据

## 一个命令生成一份完整研究快照

```bash
python scripts/run_research.py --config examples/workbench.json --out output
```

会创建新的 `output/run-…/`，重复运行保留之前的报告。可以从其他目录运行：把脚本、配置和输出参数换成相应绝对路径，CSV 路径仍相对配置文件解析。

| 文件 | 内容 |
|---|---|
| REPORT.html | 可直接打开的深色研究面板，含指标、价格折线、分歧、缺口、下次检查和可展开明细；无外部资源 |
| REPORT.md | 便于笔记、版本管理和分享的文字报告 |
| bundle.json | 结构计算、领域分析、高级分析、来源声明、输入哈希和生成时间 |
| inputs/ | 本次实际计算使用的 CSV 原始字节快照 |
| config.snapshot.json | 路径已改为 inputs/ 的重跑配置，摆脱原始输入位置 |
| COMPLETE.json | 只有所有输出写完才产生的完成标记；缺少时视为未完成导出 |

查看已运行的 [模拟报告](../examples/workbench/REPORT.md)、[完整 JSON](../examples/workbench/bundle.json)；下载 [HTML 文件](../examples/workbench/REPORT.html) 后在浏览器打开。GitHub 文件页展示源码，需要下载才能查看本地面板。

重跑一份冻结报告：

```bash
python scripts/run_research.py --config examples/workbench/config.snapshot.json --out output
```

## 换成自己的数据

复制 examples/workbench.json，修改 instrument、as_of、files 和 options，保持 skill 名及必需输入角色。`schema_version=1`；`data_kind` 使用 `imported_observations`；`max_bar_age_hours` 是使用者选择的陈旧阈值，周末和停市仍需按目标市场日历解释。面板工具的 `max_panel_age_days` 用日历日判断，不冒充交易日检查。

导入模式必须为每个文件角色填写来源名称和取数时间，可选真实来源链接。例如：

```json
"sources": {
  "bars": {
    "name": "实际使用的数据提供者与具体代码/合约、单位、周期",
    "retrieved_at": "2026-10-25T10:00:00+08:00",
    "url": "https://实际来源页面"
  }
}
```

上面是字段示意，使用时填实际信息；其余输入角色同样填写。历史研究还需保存当时可知版本与发布时间，下载时间不能代替公布时间。名称、哈希和来源链接记录来源声明，工具不认证它们为真。

旧的单项命令仍可用，新工作台复用相同计算函数。新的报告是结构化研究快照，不是仓位指令、收益回测或预测评分。

## 用在三种研究任务中

盘前计划：给明确数据截止时刻，记录当前背景、待确认条件、失效条件和下一次复查事件。尚未发生的观察结果留空。

事件研判：拆开事件事实、传导假设和价格反应。用同一截止时刻检查已公布数据，报告不能用后来的信息补强当时判断。

盘后复盘：从旧报告的冻结配置重跑以复核原计算，再用新输入产生新报告，逐项说明原假设是否被支持、反证或仍待观察。保留旧报告，不能用新结论覆盖旧计划。

## 黄金：金银与宏观对照

`scripts/analyze_gold_drivers.py` 读取 `series,observation_date,available_at,value,unit`。

| series | unit | 口径 |
|---|---|---|
| XAUUSD | USD_per_troy_ounce | 同来源的美元/金衡盎司黄金报价 |
| XAGUSD | USD_per_troy_ounce | 同单位白银报价，用于金银比 |
| DXY | index_points | 美元指数点位，不可用其他广义美元指数冒名替代 |
| US10Y_REAL | percent | 10年实际收益率的百分数数值，2.1表示2.1%，可为负 |

observation_date 是 YYYY-MM-DD 的供应商观测日期；available_at 带时区，表示该版本何时可知，不能把统计日期当公布日期。该文件约定要求观测日不晚于 available_at 的 UTC 日期。每个 series/date 仅提供一个截止时点版本，重复版本报错。

工具先按公布时间截断，再选择四类数据均完整的最早与最晚共同日期，不向前填充。少于两个完整日期就停止。价格变化是区间收益；收益率变化为 `(末值−初值)×100` 基点。端点比较没有计算相关系数，也不证明因果。

```bash
python scripts/analyze_gold_drivers.py --csv examples/macro.csv --as-of 2024-01-09T15:00:00+08:00 --data-kind synthetic --out output/gold-drivers.json
```

演示数据中黄金+2%、白银−4%、美元+1%、实际利率+10bp，金银比80→85。报告保留黄金与美元/实际利率同涨的分歧，不机械生成看空分数。这里所有价格和日期均为构造样例。

实际利率可参考 [FRED DFII10](https://fred.stlouisfed.org/series/DFII10) 的单位与观测约定；它是通胀保值国债收益率口径，并非名义利率减去任意当期通胀。获取历史版本时还需核对首次公布与修订信息，本工具不自动认证输入。
