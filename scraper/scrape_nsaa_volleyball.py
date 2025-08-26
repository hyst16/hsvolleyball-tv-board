#!/usr/bin/env python3
import json, time, re, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUT = Path("data/volleyball.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

CLASS_URLS = {
    "A":  "https://nsaa-static.s3.amazonaws.com/calculate/showclassvbA.html",
    "B":  "https://nsaa-static.s3.amazonaws.com/calculate/showclassvbB.html",
    "C1": "https://nsaa-static.s3.amazonaws.com/calculate/showclassvbC1.html",
    "C2": "https://nsaa-static.s3.amazonaws.com/calculate/showclassvbC2.html",
    "D1": "https://nsaa-static.s3.amazonaws.com/calculate/showclassvbD1.html",
    "D2": "https://nsaa-static.s3.amazonaws.com/calculate/showclassvbD2.html",
}

def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

def fetch(url: str) -> str:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text

def _cells(tr):
    # collect text from th or td; NSAA often uses <td> for header row
    return [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]

def parse_class_page(html: str, cls_code: str):
    soup = BeautifulSoup(html, "lxml")
    by_team = {}

    # Each team table has a <caption><b>Team (x-y)</b></caption>
    for cap in soup.find_all("caption"):
        team_display = cap.get_text(strip=True)
        table = cap.find_parent("table")
        if not table:
            continue

        team_name = re.sub(r"\s*\([\d\-]+\)\s*$", "", team_display).strip()
        key = norm(team_name)

        # ---- locate the header row (could be <td> or <th>)
        headers = []
        header_tr = None
        for tr in table.find_all("tr"):
            cells = _cells(tr)
            if not cells:
                continue
            # normalize plural header to singular for our field map
            cells_norm = [c.replace("Opponents", "Opponent") for c in cells]
            if "Date" in cells_norm and "Opponent" in cells_norm:
                headers = cells_norm
                header_tr = tr
                break
        if not headers or not header_tr:
            # no usable header -> skip this table
            continue

        # column index helper
        def idx(col):
            try:
                return headers.index(col)
            except ValueError:
                return None

        i_date  = idx("Date")
        i_opp   = idx("Opponent")
        i_cls   = idx("Class")
        i_wlopp = idx("W-L")
        i_wl    = idx("W/L")
        i_score = idx("Score")
        i_pts   = idx("Points")
        i_tn    = idx("Tournament Name")
        i_tloc  = idx("Tournament Location")
        i_site  = idx("Site")
        i_time  = idx("Time")
        i_ha    = idx("Home/Away")
        i_div   = idx("Div")

        rows = []
        for tr in header_tr.find_next_siblings("tr"):
            tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if not tds:
                continue

            # stop when we hit the totals block
            if any(("Total Points" in x) or ("Average Points" in x) or ("Win %" in x) for x in tds):
                break
            # skip the HR separator row: often a single TD with <hr>
            if len(tds) == 1 and ("hr" in tds[0].lower() or tds[0] == "-"):
                continue

            def val(i):
                return tds[i] if i is not None and i < len(tds) else None

            row = {}
            if i_date is not None:  row["Date"] = val(i_date)
            if i_opp  is not None:  row["Opponent"] = val(i_opp)
            if i_cls  is not None:  row["Class"] = val(i_cls)
            if i_wlopp is not None: row["W-L"] = val(i_wlopp)
            if i_wl   is not None:  row["W/L"] = val(i_wl)
            if i_score is not None: row["Score"] = val(i_score)
            if i_pts  is not None:  row["Points"] = val(i_pts)
            if i_tn   is not None:  row["Tournament Name"] = val(i_tn)
            if i_tloc is not None:  row["Tournament Location"] = val(i_tloc)
            if i_site is not None:  row["Site"] = val(i_site)
            if i_time is not None:  row["Time"] = val(i_time)
            if i_ha   is not None:  row["Home/Away"] = val(i_ha)
            if i_div  is not None:  row["Div"] = val(i_div)

            # attach helpers the UI expects
            row["_team"] = team_name
            row["_team_display"] = team_display
            row["_class"] = (row.get("Class") or cls_code)

            # skip blank-ish rows
            if not any(v and v != "-" for v in row.values()):
                continue

            rows.append(row)

        if rows:
            by_team[key] = rows

    return by_team

def main():
    all_by_team = {}
    for cls, url in CLASS_URLS.items():
        try:
            html = fetch(url)
            got = parse_class_page(html, cls)
            all_by_team.update(got)
        except Exception as e:
            print(f"[WARN] {cls} failed: {e}", file=sys.stderr)

    OUT.write_text(json.dumps({"updated": int(time.time()), "by_team": all_by_team},
                              ensure_ascii=False),
                   encoding="utf-8")
    print(f"Wrote {OUT.resolve()}")

if __name__ == "__main__":
    main()
