#!/usr/bin/env python3
"""
Kaggle 대회 목록을 공식 API에서 받아 '대회 레이더' 공용 스키마로 정규화해
kaggle.json 으로 저장한다.

인증: 환경변수 KAGGLE_USERNAME / KAGGLE_KEY (GitHub Actions secrets)
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
import base64
from datetime import datetime, timezone

API = "https://www.kaggle.com/api/v1/competitions/list"
USD_KRW = 1380  # 점수 계산용 고정 환율. 정밀할 필요 없고, 자릿수만 맞으면 된다.

USER = os.environ.get("KAGGLE_USERNAME", "")
KEY = os.environ.get("KAGGLE_KEY", "")
if not USER or not KEY:
    sys.exit("KAGGLE_USERNAME / KAGGLE_KEY 가 설정되지 않았습니다.")


def get(page):
    url = f"{API}?group=general&category=all&sortBy=latestDeadline&page={page}"
    token = base64.b64encode(f"{USER}:{KEY}".encode()).decode()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {token}",
        "User-Agent": "competition-radar/1.0",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def parse_prize(reward):
    """'$25,000' -> 25000 USD. 'Knowledge'/'Swag'/None -> None."""
    if not reward or not isinstance(reward, str):
        return None
    m = re.search(r"\$\s*([\d,]+)", reward)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def iso(v):
    """Kaggle 은 '2026-09-30T23:59:00Z' 형태로 준다. 그대로 두되 형식만 통일."""
    if not v:
        return None
    v = str(v).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(v).astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


TAG_RULES = [
    ("forensic", r"forensic|dfir|incident|malware|memory dump|disk image"),
    ("security", r"security|adversarial|attack|fraud|anomaly|intrusion|deepfake|spoof"),
    ("llm", r"\bllm\b|language model|prompt|rag|transformer|nlp|text"),
    ("cv", r"image|vision|segmentation|object detection|video|ocr|photo"),
    ("timeseries", r"time.?series|forecast|demand|sales"),
    ("tabular", r"tabular|playground|regression|classification"),
]


def tags_for(text):
    low = (text or "").lower()
    return [t for t, pat in TAG_RULES if re.search(pat, low)]


def normalize(c):
    ref = c.get("ref") or ""
    slug = ref.split("/")[-1] if ref else str(c.get("id", ""))
    deadline = iso(c.get("deadline"))
    reg = iso(c.get("mergerDeadline")) or iso(c.get("newEntrantDeadline"))
    usd = parse_prize(c.get("reward"))
    blob = f"{c.get('title', '')} {c.get('description', '')}"

    now = datetime.now(timezone.utc).isoformat()
    status = "open"
    if deadline and deadline < now:
        status = "closed"

    return {
        "id": f"kaggle:{slug}",
        "source": "kaggle",
        "title": c.get("title") or slug,
        "url": c.get("url") or f"https://www.kaggle.com/c/{slug}",
        "status": status,
        "reg_deadline": reg,
        "start": iso(c.get("enabledDate")),
        "end": deadline,
        "prize_krw": usd * USD_KRW if usd else None,
        "prize_raw": c.get("reward"),
        "weight": None,
        "onsite": False,
        "open_to_all": True,
        "teams": c.get("teamCount"),
        "tags": tags_for(blob),
        "category": c.get("category"),
    }


def main():
    events, seen = [], set()
    for page in range(1, 5):  # 페이지당 20건. 4페이지면 활성 대회는 다 덮는다.
        try:
            batch = get(page)
        except urllib.error.HTTPError as e:
            sys.exit(f"Kaggle API {e.code}: {e.read().decode()[:300]}")
        if not batch:
            break
        for c in batch:
            ev = normalize(c)
            if ev["id"] in seen:
                continue
            seen.add(ev["id"])
            events.append(ev)
        if len(batch) < 20:
            break

    # 이미 끝난 지 오래된 건 버린다 — 레이더가 볼 이유가 없다.
    events = [e for e in events if e["status"] != "closed"]
    events.sort(key=lambda e: e["end"] or "9999")

    out = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(events),
        "events": events,
    }
    with open("kaggle.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{len(events)}건 저장")


if __name__ == "__main__":
    main()
