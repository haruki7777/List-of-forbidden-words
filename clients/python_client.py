import os
import requests

API_URL = os.getenv("MODERATION_API_URL", "http://localhost:8000/v1/check")
API_KEY = os.getenv("MODERATION_API_KEY", "")


def check_forbidden_words(text: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    response = requests.post(API_URL, json={"text": text}, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    result = check_forbidden_words("홍보 문구 테스트입니다")
    print(result)
