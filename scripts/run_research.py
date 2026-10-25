#!/usr/bin/env python3
"""Run this skill's offline research pipeline and export a frozen, readable research bundle."""
import argparse
from datetime import datetime, timezone
from html import escape
import hashlib
import json
from pathlib import Path
import uuid

from analyze_structure import analyze as structure
from market_io import timestamp, number, kind

SKILL = 'gold-research-skill'
TITLES = {'gold-research-skill':'黄金研究工作台','crude-oil-research-skill':'原油研究工作台',
          'ec-shipping-research-skill':'欧线 EC 研究工作台','a-share-index-research-skill':'大 A 股指研究工作台'}
ROLES = {'gold-research-skill':{'bars','macro'}, 'crude-oil-research-skill':{'bars','curve','previous_curve'},
         'ec-shipping-research-skill':{'bars','futures','settlement_index','route_scenarios'},
         'a-share-index-research-skill':{'bars','breadth','indices'}}


def pct(value):
    return f'{value*100:+.2f}%'


def calculate(config, raw):
    if config.get('schema_version')!=1 or config.get('skill')!=SKILL:
        raise ValueError('configuration schema or skill identity mismatch')
    data_kind=kind(config['data_kind'])
    cutoff=timestamp(config['as_of'])
    options=config.get('options',{})
    max_age=number(config['max_bar_age_hours'],positive=True)
    bars=structure(raw['bars'],config['instrument'],config['timeframe'],config['as_of'],data_kind,
                   options.get('support'),options.get('resistance'),options.get('reference_time'),options.get('window_bars'))
    alerts=[]
    if bars['observation_age_seconds']>max_age*3600:
        alerts.append(f"K 线已陈旧：{bars['observation_age_seconds']/3600:.1f} 小时，超过配置阈值 {max_age:g} 小时。")
    if bars['ma_ordering']=='insufficient_history' or not bars['macd']['ready']:
        alerts.append('结构历史不足：部分均线或 MACD 未就绪。')
    if bars['reference_window'] and bars['reference_window']['window_state']=='expired':
        alerts.append('人工参考窗口已过期，需要重新检查原假设。')
    metrics=[['已收盘 K 线',str(bars['completed_bar_count']),'只使用截止时刻已收盘数据'],
             ['均线排列',bars['ma_ordering'],'价格变换，不是独立胜率证明'],
             ['最新收盘',f"{bars['latest_completed_bar']['close']:g}",config['instrument']]]
    if SKILL=='gold-research-skill':
        from analyze_gold_drivers import analyze
        advanced=analyze(raw['macro'],config['as_of'],data_kind)
        domain=None
        metrics += [['黄金区间变化',pct(advanced['returns']['XAUUSD']),'共同完整日期窗口'],
                    ['实际利率变化',f"{advanced['real_yield_change_bp']:+.2f} bp",'百分数输入换算成基点'],
                    ['金银比',f"{advanced['gold_silver_ratio_end']:.3f}",'相同美元/金衡盎司口径']]
        if advanced['co_movement']['gold_up_with_dollar_and_yield_up']:
            alerts.append('黄金与美元、实际利率同涨：保留共同变化事实，不能用简单反向关系解释。')
        gaps=['宏观对照没有证明因果；资金、需求和事件证据仍需补充。']
        next_checks=['核对实际利率与美元数据的发布时间和历史版本。','检查关键位收复是否延续，失效则撤销修复假设。']
    elif SKILL=='crude-oil-research-skill':
        from analyze_curve import analyze
        from compare_curves import analyze as compare
        domain=analyze(raw['curve'],config['as_of'],data_kind)
        advanced=compare(raw['previous_curve'],raw['curve'],options['previous_as_of'],config['as_of'],data_kind)
        metrics += [['当前曲线',domain['curve_shape'],domain['benchmark']],
                    ['固定合约对价差变化',f"{advanced['matched_spread_change']:+.3f}",domain['currency']+'/桶'],
                    ['可比合约',str(len(advanced['matched_contracts'])),'剔除换月新增/移除端点']]
        if domain['quote_span_seconds']:
            alerts.append(f"曲线报价并非同时：时间跨度 {domain['quote_span_seconds']:g} 秒。")
        if advanced['added_contracts'] or advanced['dropped_contracts']:
            alerts.append('两期曲线合约集合有变化：固定比较合约对，不用新近月替代旧近月。')
        gaps=['价差变化没有单独证明库存或供需变化；需同口径库存和交付证据。']
        next_checks=['确认比较合约未到期、报价有效且流动性可用。','结合统计周和公布时点复核库存，不从曲线直接推出涨幅。']
    elif SKILL=='ec-shipping-research-skill':
        from compare_settlement import analyze
        from analyze_route_scenarios import analyze as scenario
        domain=analyze(raw['futures'],raw['settlement_index'],options['contract'],config['as_of'],data_kind)
        advanced=scenario(raw['route_scenarios'],config['as_of'],data_kind)
        metrics += [['期价−已公布指数',f"{domain['futures_minus_last_published_index']:+.3f}",'滞后参照，非同步可交易基差'],
                    ['情景数',str(len(advanced['scenarios'])),'用户假设，不是实际损失统计'],
                    ['情景最大运力损失',f"{max(x['capacity_loss_fraction'] for x in advanced['scenarios'])*100:.2f}%",'固定船队、其他条件不变']]
        if domain['index_published_after_quote']:
            alerts.append('指数在所选期货报价之后才公布：该价差不能解释成报价当时可见。')
        gaps=['绕航情景尚未计入船队调配、新船和实际货量；运力压力没有映射成运价或 EC 涨幅。']
        next_checks=['核对航路变化、运价公布与目标合约的结算观察范围。','更新需求和周转假设，检查压力是否被运力补充抵消。']
    else:
        from analyze_breadth import analyze
        from compare_index_styles import analyze as styles
        domain=analyze(raw['breadth'],config['as_of'],options['universe'],options['expected_count'],data_kind)
        advanced=styles(raw['indices'],config['as_of'],data_kind)
        metrics += [['样本覆盖',f"{domain['observed_count']}/{domain['expected_count']}",'数量齐全也不认证成分身份'],
                    ['样本上涨比例',f"{domain['advance_fraction']*100:.2f}%",'以已包含成分为分母'],
                    ['区间领先指数',advanced['ranked_by_price_return'][0],'四个现货价格指数共同窗口']]
        if not domain['declared_sample_complete']:
            alerts.append(f"样本覆盖率仅 {domain['coverage']*100:.1f}%，不能扩写为全市场。")
        gaps=['风格与宽度的观察窗口需分别核对，不从共时变化直接推断因果或全市场普涨。']
        next_checks=['补齐当时成分及缺失样本，检查权重与等权分歧。','讨论股指期货前另查具体合约、同期现货和基差。']
    if 'end_date_age_days' in advanced:
        limit=number(options['max_panel_age_days'],positive=True)
        if advanced['end_date_age_days']>limit:
            alerts.append(f"对照面板末日距截止日 {advanced['end_date_age_days']} 天，超过配置阈值 {limit:g} 天。")
    if data_kind=='synthetic':
        alerts.insert(0,'SIMULATION / 全部为构造数据：展示计算与研究流程，不是历史预测或交易业绩。')
    return {'schema_version':1,'skill':SKILL,'title':TITLES[SKILL],'data_kind':data_kind,
            'as_of_utc':cutoff.isoformat(),'metrics':metrics,'attention':alerts,'evidence_gaps':gaps,
            'next_checks':next_checks,'structure':bars,'domain':domain,'advanced':advanced,
            'scope':'Offline descriptive research; imported source claims are not authenticated; no execution or profit estimate.'}


def load(config_path):
    config_path=Path(config_path).resolve()
    config_raw=config_path.read_bytes()
    config=json.loads(config_raw.decode('utf-8-sig'))
    if config.get('skill')!=SKILL or set(config.get('files',{}))!=ROLES[SKILL]:
        raise ValueError('configuration must declare the exact input roles for this skill')
    data_kind=kind(config['data_kind'])
    raw, provenance={},{}
    for role,value in config['files'].items():
        if not isinstance(value,str) or not value.strip():
            raise ValueError('input paths must be nonempty strings')
        path=(config_path.parent/value).resolve()
        content=path.read_bytes()
        source=config.get('sources',{}).get(role)
        if data_kind=='imported_observations':
            if not isinstance(source,dict) or not str(source.get('name','')).strip() or 'retrieved_at' not in source:
                raise ValueError(f'imported data needs sources.{role}.name and retrieved_at')
            timestamp(source['retrieved_at'])
        else:
            source={'name':'Constructed synthetic example','url':'synthetic://local-example'}
        raw[role]=content
        provenance[role]={'source':source,'file_name':path.name,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}
    result=calculate(config,raw)
    result['inputs']=provenance
    result['config_sha256']=hashlib.sha256(config_raw).hexdigest()
    return config,raw,result


def markdown(result):
    rows=['# '+result['title'],'',f"数据标签：**{result['data_kind']}** · 截止：`{result['as_of_utc']}`",'',
          '| 观测 | 数值 | 解读范围 |','|---|---|---|']
    for row in result['metrics']:
        rows.append('| '+' | '.join(str(value).replace('|','\\|').replace('\n',' ') for value in row)+' |')
    for title,key in [('需要注意','attention'),('证据缺口','evidence_gaps'),('下次检查','next_checks')]:
        rows+=['','## '+title,'']
        rows += ['- '+str(value) for value in result[key]] or ['- 本次未触发配置检查项；这不证明数据完整或策略有效。']
    rows+=['','## 可复查文件','','[完整计算与来源](bundle.json) · [浏览器报告](REPORT.html) · [冻结输入](inputs/)','',
           '报告是描述性研究快照；原始输入、来源声明和哈希随结果保存。导入标签与本地校验不能认证数据来源或证明当时版本。']
    return '\n'.join(rows)+'\n'


def html_report(result,raw):
    e=lambda value:escape(str(value),quote=True)
    cards=''.join(f'<article><p>{e(label)}</p><strong>{e(value)}</strong><small>{e(note)}</small></article>' for label,value,note in result['metrics'])
    sections=''.join(f'<section><h2>{e(title)}</h2><ul>'+(''.join(f'<li>{e(item)}</li>' for item in result[key]) or '<li>本次未触发配置检查项；不等于已证明完整或有效。</li>')+'</ul></section>'
                     for title,key in [('需要注意','attention'),('证据缺口','evidence_gaps'),('下次检查','next_checks')])
    from analyze_structure import load_bars
    bars,_=load_bars(raw['bars'],timestamp(result['as_of_utc']))
    values=[bar['close'] for bar in bars]
    low,high=min(values),max(values)
    span=high-low
    points=' '.join(f'{20+760*i/max(1,len(values)-1):.2f},{140-(v-low)/span*110 if span else 85:.2f}' for i,v in enumerate(values))
    chart=f'<svg viewBox="0 0 800 175" role="img" aria-label="已收盘价格相对走势"><title>已收盘价格；垂直范围 {low:g} 至 {high:g}；横轴按观测行排列，非连续时间距离</title><path d="M20 150H780" stroke="#334155"/><polyline points="{points}" fill="none" stroke="#36d8bb" stroke-width="3"/></svg>'
    detail=e(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(result['title'])}</title><style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#090e17;color:#dce5f3;font:15px/1.7 system-ui,sans-serif}}main{{max-width:1120px;margin:auto;padding:36px 20px}}a{{color:#67dfc4}}header{{border-bottom:1px solid #29364c;padding-bottom:24px}}h1{{font-size:clamp(28px,5vw,44px);margin:10px 0}}.tag{{color:#67dfc4;font:12px monospace;letter-spacing:2px}}.meta,small{{color:#9baac2}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:24px 0}}article,section,details,.chart{{background:#111b2b;border:1px solid #29364c;border-radius:10px;padding:18px;margin-bottom:14px}}article p{{margin:0;color:#9baac2}}strong{{display:block;font:26px/1.6 monospace;color:#e2faf4}}small{{display:block}}h2{{font-size:18px;margin:0 0 12px}}ul{{padding-left:22px}}li{{margin:8px 0}}svg{{display:block;width:100%;height:auto}}pre{{overflow:auto;max-height:480px;font-size:12px}}footer{{color:#9baac2;font-size:13px}}@media print{{:root{{color-scheme:light}}body{{background:#fff;color:#111}}article,section,details,.chart{{background:#fff;border-color:#ccc;break-inside:avoid}}strong,.meta,small,footer,a{{color:#222}}details{{display:none}}}}
</style><main><header><div class="tag">SERENNITY007 / RESEARCH WORKBENCH</div><h1>{e(result['title'])}</h1><p class="meta">{e(result['data_kind'])} · 截止 {e(result['as_of_utc'])}</p><a href="REPORT.md">Markdown</a> · <a href="bundle.json">完整 JSON</a></header><div class="grid">{cards}</div><div class="chart"><h2>价格观察</h2>{chart}<small>范围 {low:g}–{high:g}；横轴按已收盘观测排序。无买卖点标注。</small></div>{sections}<details><summary>计算明细与输入来源</summary><pre>{detail}</pre></details><footer>离线生成，无外部字体、脚本和行情请求。构造样例不能作为交易业绩；导入数据仍需核对来源和版本。</footer></main></html>'''


def run(config_path,output):
    config,raw,result=load(config_path)
    result['generated_at_utc']=datetime.now(timezone.utc).isoformat()
    md=markdown(result)
    page=html_report(result,raw)
    payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    directory=Path(output)/('run-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    directory.mkdir(parents=True,exist_ok=False)
    (directory/'inputs').mkdir()
    for role,content in raw.items():
        (directory/'inputs'/f'{role}.csv').write_bytes(content)
    snapshot=dict(config,files={role:f'inputs/{role}.csv' for role in raw})
    artifacts={'bundle.json':payload,'REPORT.md':md,'REPORT.html':page,
               'config.snapshot.json':json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n'}
    for name,body in artifacts.items():
        with (directory/name).open('x',encoding='utf-8',newline='\n') as handle:
            handle.write(body)
    (directory/'COMPLETE.json').write_text(json.dumps({'status':'complete','files':list(artifacts),'input_roles':sorted(raw)})+'\n',encoding='utf-8',newline='\n')
    return directory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--json',action='store_true',help='print a machine-readable completion summary')
    args=parser.parse_args()
    try:
        directory=run(args.config,args.out)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(2,f'ERROR: {exc}\n')
    if args.json:
        print(json.dumps({'status':'complete','skill':SKILL,'directory':str(directory.resolve())},ensure_ascii=True))
    else:
        print(f'PASS / {SKILL} -> {directory / "REPORT.html"}')


if __name__=='__main__':
    main()
