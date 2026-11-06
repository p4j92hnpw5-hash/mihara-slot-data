import json
import re
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from html.parser import HTMLParser

URL = "https://slo-navi.com/data/2026-11-02"
TZ = ZoneInfo("Asia/Tokyo")

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

def get_rows(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        html = res.read().decode("utf-8", errors="replace")
    parser = TableReader()
    parser.feed(html)
    return parser.rows

def parse_number(value):
    value = value.replace(",", "").replace("+", "").strip()
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return None

def main():
    today = datetime.now(TZ).date()
    dates = [
        (today - timedelta(days=i)).isoformat()
        for i in range(7, 0, -1)
    ]

    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    for machine in data.get("machines", []):
        machine["days"] = {
            d: machine.get("days", {}).get(d)
            for d in dates
            if isinstance(machine.get("days", {}).get(d), int)
        }

    # URLの対象日・店舗と取得構造が未検証のため、
    # 現時点では未確認の数値を書き込まない。
    data["dates"] = dates
    data["updated"] = datetime.now(TZ).isoformat()
    data["source"] = "自動更新準備中（差枚未取得）"

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()