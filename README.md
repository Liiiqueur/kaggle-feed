# kaggle-feed

「대회 레이더」의 Kaggle 담당 위성.

Kaggle 대회 목록은 공식 API 토큰이 있어야 읽을 수 있고, 레이더가 도는 환경에서는
kaggle.com 으로 직접 나가는 트래픽이 막혀 있다. 그래서 이 리포가 매일 한 번 대신 받아
`kaggle.json` 으로 커밋해 두고, 레이더는 raw 파일 한 줄만 읽어 간다.

CTFtime 과 DACON 은 레이더가 직접 읽으므로 이 리포와 무관하다.

## 설정 (한 번만)

**1. 리포 만들기**

이름은 아무거나. `kaggle-feed` 를 쓴다고 가정한다. **Private 으로 만들면 raw 링크를
레이더가 못 읽으니 Public 으로 만든다.** (담기는 건 Kaggle 공개 대회 목록뿐이고,
토큰은 파일이 아니라 시크릿에 들어가므로 노출되지 않는다.)

이 폴더의 세 파일을 그대로 올린다.

```
fetch.py
README.md
.github/workflows/fetch.yml
```

**2. Kaggle API 토큰 발급**

kaggle.com → 우상단 프로필 → Settings → API → **Create New Token**.
`KGAT_...` 형태의 토큰 문자열 하나가 발급된다. 다시 볼 수 없으니 그 자리에서 복사해 둔다.

**3. 리포 시크릿에 등록**

리포 → Settings → Secrets and variables → Actions → New repository secret.
하나만 만든다.

| Name | Value |
|---|---|
| `KAGGLE_API_TOKEN` | 위에서 복사한 `KGAT_...` 토큰 전체 |

토큰은 시크릿에 등록한 뒤로는 어디에도 평문으로 남겨두지 않는다. 대화창이나 메모장에
붙여넣었던 사본이 있다면 지운다 — 토큰이 그런 곳에 남았다고 의심되면 Kaggle 설정에서
기존 토큰을 폐기하고 새로 하나 발급받아 시크릿 값만 갱신하면 된다.

**4. 첫 실행**

리포 → Actions 탭 → `kaggle-feed` → **Run workflow**.
1~2분 뒤 루트에 `kaggle.json` 이 커밋되어 있으면 성공이다.

**5. 레이더에 주소 알려주기**

아래 주소를 확인하고 Claude 에게 알려주면 매일 이 파일을 읽도록 연결된다.

```
https://raw.githubusercontent.com/<GitHub아이디>/kaggle-feed/main/kaggle.json
```

기본 브랜치가 `master` 면 `main` 자리를 바꾼다.

## 이후

손댈 일 없다. 매일 07:00 KST 근처에 돌고, 목록에 변화가 없는 날은 커밋조차 남기지 않는다.

동작이 궁금하면 Actions 탭의 최근 실행 로그를 보면 되고, 실패하면 GitHub 이 메일로 알려준다.
며칠 밀리면 레이더 대시보드 하단의 "Kaggle 갱신" 시각으로도 바로 보인다.

## 출력 형식

```json
{
  "fetched_at": "2026-09-08T22:00:11+00:00",
  "count": 14,
  "events": [
    {
      "id": "kaggle:playground-series-s6e9",
      "source": "kaggle",
      "title": "Predicting Electric Vehicle Purchases",
      "url": "https://www.kaggle.com/c/playground-series-s6e9",
      "status": "open",
      "reg_deadline": null,
      "start": "2026-09-01T00:00:00+00:00",
      "end": "2026-09-30T23:59:00+00:00",
      "prize_krw": null,
      "prize_raw": "Swag",
      "weight": null,
      "onsite": false,
      "open_to_all": true,
      "teams": 1832,
      "tags": ["tabular"],
      "category": "Playground"
    }
  ]
}
```

`prize_krw` 는 상금이 달러로 표기된 경우에만 채워지고(고정 환율 1,380원), `Knowledge`
나 `Swag` 처럼 금액이 아닌 보상은 `null` 로 두고 `prize_raw` 에 원문을 남긴다.
