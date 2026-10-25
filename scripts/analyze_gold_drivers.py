#!/usr/bin/env python3
"""Compare gold, silver, dollar and real-yield observations available at an explicit cutoff."""
import argparse
from datetime import date
from pathlib import Path

from market_io import timestamp, number, records, provenance, emit, kind

UNITS = {'XAUUSD':'USD_per_troy_ounce', 'XAGUSD':'USD_per_troy_ounce',
         'DXY':'index_points', 'US10Y_REAL':'percent'}


def analyze(raw, as_of, data_kind):
    cutoff = timestamp(as_of)
    panel, seen, excluded = {}, set(), 0
    for row in records(raw, ['series','observation_date','available_at','value','unit']):
        available = timestamp(row['available_at'])
        if available > cutoff:
            excluded += 1
            continue
        series = row['series']
        day = date.fromisoformat(row['observation_date'])
        if series not in UNITS or row['unit'] != UNITS[series]:
            raise ValueError('series and units must match XAUUSD/XAGUSD/DXY/US10Y_REAL contract')
        if day > available.date():
            raise ValueError('observation date cannot be after availability UTC date')
        identity = series, day
        if identity in seen:
            raise ValueError('duplicate series/date; supply one as-of vintage per observation')
        seen.add(identity)
        panel.setdefault(day, {})[series] = {'value':number(row['value'],positive=series!='US10Y_REAL'),
                                            'available_at':available.isoformat()}
    complete = sorted(day for day, values in panel.items() if set(values)==set(UNITS))
    if len(complete) < 2:
        raise ValueError('at least two complete common observation dates are required; no forward filling')
    start, end = complete[0], complete[-1]
    first, last = panel[start], panel[end]
    changes = {series:last[series]['value']/first[series]['value']-1 for series in ('XAUUSD','XAGUSD','DXY')}
    yield_bp = (last['US10Y_REAL']['value']-first['US10Y_REAL']['value'])*100
    gold_up, dollar_up, rates_up = changes['XAUUSD']>0, changes['DXY']>0, yield_bp>0
    return {'schema_version':1,'data_kind':kind(data_kind),'as_of_utc':cutoff.isoformat(),
            'start_date':start.isoformat(),'end_date':end.isoformat(),'complete_dates':len(complete),
            'incomplete_dates':len(panel)-len(complete),'excluded_unavailable_rows':excluded,
            'observations':{day.isoformat():panel[day] for day in (start,end)},
            'returns':changes,'real_yield_change_bp':yield_bp,
            'gold_silver_ratio_start':first['XAUUSD']['value']/first['XAGUSD']['value'],
            'gold_silver_ratio_end':last['XAUUSD']['value']/last['XAGUSD']['value'],
            'co_movement':{'gold_up':gold_up,'dollar_up':dollar_up,'real_yield_up':rates_up,
                           'gold_up_with_dollar_and_yield_up':gold_up and dollar_up and rates_up},
            'end_date_age_days':(cutoff.date()-end).days,'source_sha256':provenance(raw),
            'scope':'Same-date descriptive comparison; no causal attribution, predictive score or forward fill.',
            'limitations':['Imported available_at and observation vintages are not independently authenticated',
                           'DXY is not a substitute for a different broad dollar index; real yield is not nominal yield',
                           'Only common dates are compared; an endpoint return is not a correlation estimate']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',type=Path,required=True)
    parser.add_argument('--as-of',required=True)
    parser.add_argument('--data-kind',choices=('synthetic','imported_observations'),required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:
        emit(analyze(args.csv.read_bytes(),args.as_of,args.data_kind),args.out,[args.csv])
    except (ValueError,OSError,KeyError) as exc:
        parser.exit(2,f'ERROR: {exc}\n')
    print('Saved gold/silver and macro comparison.')


if __name__=='__main__':
    main()
