const API_URL = process.env.MODERATION_API_URL || "http://localhost:8000/v1/check";
const API_KEY = process.env.MODERATION_API_KEY || "";

async function checkForbiddenWords(text) {
  const headers = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const response = await fetch(API_URL, {
    method: "POST",
    headers,
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Moderation API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

async function main() {
  const result = await checkForbiddenWords("홍보 문구 테스트입니다");
  console.log(result);
}

if (require.main === module) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { checkForbiddenWords };
