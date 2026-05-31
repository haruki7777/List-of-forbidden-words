# List of Forbidden Words

금지어 목록을 JSON으로 관리하고, HTTP API로 문장/댓글/채팅 메시지를 검사할 수 있는 작은 서버입니다.

> 주의: 세상 모든 금지어를 완전히 포함하는 목록은 존재하기 어렵습니다. 은어, 오타, 초성, 띄어쓰기 우회, 신조어가 계속 생기므로 이 저장소는 **계속 추가/관리하는 방식**으로 쓰는 것을 권장합니다.

## 중요한 운영 원칙

공개 GitHub 저장소에는 민감 표현 원본 전체 목록을 그대로 올리지 않는 것을 권장합니다.

- 외부 위키/웹페이지 내용을 그대로 복사해 저장하면 라이선스와 저작권 문제가 생길 수 있습니다.
- 민감 표현 원문을 공개 목록으로 배포하면 재유포 위험이 있습니다.
- 공개 저장소에는 API 코드, 데이터 형식, 샘플 규칙, 변환 도구만 둡니다.
- 실제 운영용 목록은 서버의 비공개 파일, 비공개 저장소, DB, 환경별 볼륨에서 관리합니다.

## 기능

- FastAPI 기반 금지어 감지 API
- JavaScript / Python 어디서든 HTTP 요청으로 사용 가능
- 단어, 정규식 패턴, 카테고리, 심각도 지원
- 한글/영문 대소문자, 유니코드 정규화, 공백 제거 비교 지원
- 선택적 API Key 보호 지원
- 기본값으로 감지된 원문을 마스킹해서 응답

## 폴더 구조

```txt
.
├─ app/
│  ├─ main.py
│  └─ moderator.py
├─ data/
│  └─ forbidden_words.ko.json
├─ clients/
│  ├─ javascript.js
│  └─ python_client.py
├─ integrations/
│  └─ discord_py_example.py
├─ tools/
│  └─ build_rules_from_csv.py
├─ requirements.txt
├─ Dockerfile
├─ .env.example
└─ README.md
```

## 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

문서 확인:

```txt
http://localhost:8000/docs
```

## API 사용

```bash
curl -X POST http://localhost:8000/v1/check \
  -H "Content-Type: application/json" \
  -d '{"text":"검사할 문장입니다"}'
```

## API Key 사용

`.env` 또는 서버 환경변수에 설정합니다.

```env
MODERATION_API_KEY=your-secret-key
```

요청 헤더에 넣습니다.

```bash
curl -X POST http://localhost:8000/v1/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"text":"검사할 문장"}'
```

API Key를 설정하지 않으면 공개 API처럼 동작합니다.

## 금지어 추가 방법

`data/forbidden_words.ko.json`에 항목을 추가하면 됩니다.

```json
{
  "id": "custom_001",
  "type": "word",
  "value": "추가할단어",
  "category": "custom",
  "severity": 3,
  "enabled": true,
  "description": "내 서비스에서 금지할 단어"
}
```

정규식도 가능합니다.

```json
{
  "id": "custom_regex_001",
  "type": "regex",
  "value": "홍보\\s*문구",
  "category": "spam",
  "severity": 2,
  "enabled": true,
  "description": "홍보성 문구 패턴"
}
```

## CSV에서 목록 만들기

직접 정리한 CSV를 JSON 규칙 파일로 변환할 수 있습니다.

CSV 헤더:

```csv
id,type,value,category,severity,enabled,description
```

변환:

```bash
python tools/build_rules_from_csv.py --input ./my_rules.csv --output ./data/forbidden_words.ko.json
```

운영 서버에서 비공개 파일을 쓰고 싶으면 환경변수로 지정합니다.

```env
FORBIDDEN_WORDS_PATH=/secure/path/forbidden_words.private.json
```

## JavaScript에서 사용

```js
const result = await fetch("http://localhost:8000/v1/check", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "검사할 메시지" })
}).then(r => r.json());

if (result.blocked) console.log("차단됨", result.matches);
```

## Python에서 사용

```py
import requests

res = requests.post("http://localhost:8000/v1/check", json={"text": "검사할 메시지"})
print(res.json())
```

## Discord 봇에 붙이는 방식

`integrations/discord_py_example.py`를 참고하세요. 메시지를 받았을 때 `/v1/check`로 보내고, `blocked`가 `true`면 삭제/경고 처리하면 됩니다.

## 운영 팁

- 단순 단어 목록만으로는 우회 입력을 모두 막을 수 없습니다.
- 초성/띄어쓰기/특수문자/반복문자 우회가 있으면 regex 항목을 추가하세요.
- 차단 로그를 따로 남겨서 자주 나오는 우회 표현을 목록에 계속 추가하세요.
- 공개 API로 둘 경우 악용될 수 있으니 실서비스에서는 API Key를 권장합니다.
- API 응답에서 원문을 보고 싶으면 `RETURN_MATCH_VALUE=true`를 설정할 수 있지만, 운영 환경에서는 기본값인 마스킹을 권장합니다.
