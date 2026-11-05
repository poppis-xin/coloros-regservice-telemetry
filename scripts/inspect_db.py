#!/usr/bin/env python3
"""只读分析 com.coloros.regservice 的 cmcc_dm.db。

只打印表结构、行数与脱敏样本，不会输出个人数据（应用名、SSID、ICCID 等）。

用法:
    python3 inspect_db.py path/to/cmcc_dm.db
"""
import sqlite3
import sys


def mask(value, keep=0):
    s = '' if value is None else str(value)
    if not s:
        return s
    if len(s) <= keep:
        return '*' * len(s)
    return s[:keep] + '*' * (len(s) - keep)


def main(path):
    con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    cur = con.cursor()

    cur.execute("select name, type from sqlite_master where type in ('table','view') order by name")
    rows = cur.fetchall()

    print(f"# {path}")
    print(f"# tables: {len(rows)}\n")

    for name, typ in rows:
        try:
            cur.execute(f'select count(*) from "{name}"')
            n = cur.fetchone()[0]
        except Exception as e:
            n = f'? ({e})'
        print(f'[{typ}] {name:<40} rows={n}')

        cur.execute(f'pragma table_info("{name}")')
        cols = [c[1] for c in cur.fetchall()]
        if cols:
            print('        cols: ' + ', '.join(cols))

        if typ == 'table' and isinstance(n, int) and n > 0:
            cur.execute(f'select * from "{name}" limit 1')
            row = cur.fetchone()
            if row:
                pairs = []
                for col, val in zip(cols, row):
                    if isinstance(val, (int, float)):
                        pairs.append(f'{col}={val}')
                    else:
                        pairs.append(f'{col}={mask(val)!r}')
                print('        sample(redacted): ' + '; '.join(pairs)[:600])
        print()

    con.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
