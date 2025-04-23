import os, sys, textwrap
from openai import OpenAI
from dotenv import load_dotenv

# ── 로컬 패키지 경로 확실히 추가 ───────────────────────
sys.path.append(os.path.abspath("."))

from peak.csv_utils import load_csv, search_companies
from peak.pdf_utils import summarize_pdf
from peak.web_utils import get_company_info          # DuckDuckGo 검색용

# ── 환경 변수 & OpenAI 클라이언트 ───────────────────────
load_dotenv()
client_1 = OpenAI(api_key=os.getenv("OPENAI_API_KEY_1"))
client_2 = OpenAI(api_key=os.getenv("OPENAI_API_KEY_2"))

# ── Agent 프롬프트 (한국어) ────────────────────────────
ai_sales_consultant_instruction = {
    "role": "system",
    "content": textwrap.dedent(
        """
        당신은 AI 기반 B2B 세일즈 컨설턴트입니다.
        클라이언트 요구와 시장 맥락을 분석해 가장 적합한 파트너 회사를 추천하고,
        기술력·시장 경쟁력·성장 가능성 근거를 제시해 설득해야 합니다.
        대화는 모두 한국어로 진행합니다.
        """
    ).strip(),
}

buyer_instruction = {
    "role": "system",
    "content": (
        "당신은 투자·파트너십 검토 담당자입니다. "
        "셀러가 제안한 회사의 사업성·기술력·시장성을 분석적으로 질문·평가하며 "
        "투자·협업 가치를 비판적으로 검토합니다. 대화는 한국어로 진행합니다."
    ),
}

# ── GPT 호출 헬퍼 ────────────────────────────────────
def chat(client, prompt, history, system_inst):
    msgs = [system_inst] + history + [{"role": "user", "content": prompt}]
    return (
        client.chat.completions.create(
            model="gpt-3.5-turbo", messages=msgs, max_tokens=500
        )
        .choices[0]
        .message.content
    )

# ── 입력 모드 & 토픽 생성 ─────────────────────────────
mode = input("대화 기반 선택 [csv / pdf / web / custom] : ").strip().lower()

if mode == "pdf":
    pdf_path = "docs/휴램프로_회사소개서.pdf"      # 필요 시 경로 수정
    topic = summarize_pdf(pdf_path)

elif mode == "csv":
    kw = input("회사명 / 업종 / 위치 / 연락처 키워드 : ")
    topic = search_companies(load_csv(), kw)

elif mode == "web":
    company = input("검색할 회사명 입력 : ")
    topic = get_company_info(company)

else:
    topic = input("AI끼리 대화할 주제 입력 : ")

# ── AI ↔ AI 대화 루프 ────────────────────────────────
turns = 5
histA, histB, last = [], [], topic
print("\n💬 AI 영업 대화 시작\n")

for i in range(turns):
    is_A = i % 2 == 0
    speaker = "AI Sales Consultant (A)" if is_A else "Buyer (B)"
    client  = client_1 if is_A else client_2
    hist    = histA if is_A else histB
    inst    = ai_sales_consultant_instruction if is_A else buyer_instruction

    print(f"{speaker} 고민 중…")
    resp = chat(client, last, hist, inst)
    print(resp, "\n")

    last = resp
    if is_A:
        histA.append({"role": "user", "content": last})
        histB.append({"role": "assistant", "content": last})
    else:
        histB.append({"role": "user", "content": last})
        histA.append({"role": "assistant", "content": last})
