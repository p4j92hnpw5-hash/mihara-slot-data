import json
import re
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from html.parser import HTMLParser

TZ = ZoneInfo("Asia/Tokyo")
BASE_URL = "https://slo-navi.com/data/"

class TableReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(self.cell.strip())
            self.cell = None
        elif tag == "tr" and self.row:
            self.rows.append(self.row)

def number(value):
    value = value.strip().replace(",", "").replace("+", "")
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return None

def fetch(date):
    url = BASE_URL + date + "-11019/"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        html = res.read().decode("utf-8", errors="replace")
    parser = TableReader()
    parser.feed(html)
    return parser.rows

def main():
    today = datetime.now(TZ).date()
    dates = [
        (today - timedelta(days=i)).isoformat()
        for i in range(7, 0, -1)
    ]

    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    machines = data.get("machines", [])
    for machine in machines:
        old = machine.get("days", {})
        machine["days"] = {
            date: old.get(date) for date in dates
        }

    for date in dates:
        try:
            rows = fetch(date)
            print(date, "HTML rows:", len(rows))
        except Exception as exc:
            print(date, "取得失敗:", str(exc))
            continue

        for row in rows:
            if len(row) < 4:
                continue
            # 機種名、台番号、G数、差枚の順番
            if not re.fullmatch(r"\d+", row[1].strip()):
                continue

            machine_no = int(row[1].strip())
            diff = number(row[3])
            if diff is None:
                continue

                        machine = next(
                (m for m in machines if m.get("number") == machine_no),
                None
            )
            if machine is None:
                machine = {
                    "number": machine_no,
                    "model": row[0],
                    "days": {d: None for d in dates}
                }
                machines.append(machine)

            machine["days"][date] = diff
            machine["model"] = row[0]
            print(date, machine_no, diff)