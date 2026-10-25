[English](README.md) · [简体中文](README.zh-CN.md)

![黄金研究](.github/cover.svg)

# 黄金研究

<!-- futures-desk-v3 -->
## v2.0 研究工作台

新增**中英双语**离线报告、历史版本与夜盘交易日约束、可比基差月差、季节证据、Decimal 费用保证金容量及跳空压力情景。[输入约定](docs/desk-data-contract.md) · [产业研究手册](references/research-playbook.md) · [容量假设](docs/desk-risk-model.md)。

```bash
python scripts/run_desk.py run --config examples/desk-demo/gold/config.json --out output --lang zh-CN
```

每次运行同时生成中英报告。下方原命令和冻结中文演示继续保留。独立 Skill ZIP 可在[发布页](https://github.com/Serennity007/gold-research-skill/releases)下载。基础命令只需 Python 3.10+。


我把黄金价格结构、金银比、美元和实际利率放在一起看。这里留了两组练习：一组检查支撑收复，另一组比较金银和宏观数据。

[涛涛的期货研究](https://github.com/Serennity007/taotao-futures-research) · [Skill 指令](SKILL.md) · MIT

## 跑一次练习

准备 Python 3.10 及以上版本，脚本只用标准库：

```bash
git clone https://github.com/Serennity007/gold-research-skill.git
cd gold-research-skill
python scripts/run_research.py --config examples/workbench.json --out output
```

打开终端打印的 `REPORT.html`。想先看结果，可以打开 [文字报告](examples/workbench/REPORT.md)，或下载 [HTML 报告](examples/workbench/REPORT.html) 后用浏览器查看。

仓库自带的 CSV 是模拟数据，日期是练习标签。这组练习可以核对计算和步骤，不能作为历史交易记录。

## 对照结果看数据

先看价格：前收盘98，末收盘102，回到人工支撑100上方；MA5、MA10、MA20仍向下排列。报告保留这两项观察。

再看宏观练习：黄金2000→2040，白银25→24，金银比80→85；美元涨1%，实际利率从2.0%到2.1%，增加10个基点。这是另一组独立模拟数据，不与前面的价格序列拼接。

你可以先核对这些数字，再读 [方法说明](references/method.md)，看看还需要哪些资料。

## 换自己的数据

复制 `examples/workbench.json`，修改标的、截止时间和文件位置。导入数据时，将 `data_kind` 改成 `imported_observations`，给每个文件填写来源名称和取数时间。[输入字段与配置](references/workbench.md) 有说明，旧的单项计算命令也保留在里面。

程序把 CSV 的相对路径按配置文件位置解析。若从其他目录运行，使用脚本和配置的绝对路径。

## 保存和复盘

每次运行会新建 `output/run-…/`。`REPORT.md` 放文字结果，`bundle.json` 放计算明细，`inputs/` 保存本次使用的文件。

在本仓库用旧报告的配置重跑：

```bash
python scripts/run_research.py --config 旧报告目录/config.snapshot.json --out output
```

把“旧报告目录”换成实际路径。输入相同，计算结果应一致。复盘时保留旧报告，再用新数据另跑一份，对照原来等的条件有没有发生。[记录格式](references/report-template.md) 可作参考。

## 作为 Skill 使用

把整个仓库放进你使用工具的技能目录，保留文件夹名 `gold-research-skill`。调用时写清数据位置、标的和截止时间：

```text
使用 $gold-research-skill，读取我提供的……，截止时间为……。
运行计算，说明已经观察到什么、还有什么要查，保存报告。
```

## 检查计算

```bash
python -m unittest discover -s tests -v
```

当前有 17 项本地测试，检查计算、时间截止和文件读写。实际数据的来源、单位与历史版本仍需要你核对。[官方资料入口](references/sources.md) 放在这里。

K 线计算沿用我在 [选股工具合集](https://github.com/Serennity007/awesome-stock-quant-skills/tree/67156b0aa4860894a8cdbc66b797db535531fe59/my-skills/gold-cross-asset-research) 中整理的脚本，本仓库附有自身代码与测试。
