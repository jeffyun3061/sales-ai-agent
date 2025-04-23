from flask import Blueprint, request, jsonify
from backend.peak.csv_utils import load_csv, search_companies
from backend.peak.pdf_utils import summarize_pdf
from backend.peak.web_utils import get_company_info
from openai import OpenAI
from dotenv import load_dotenv
import os
import textwrap

# 🔐 API Key 불러오기
load_dotenv()
client_1 = OpenAI(api_key=os.getenv("OPENAI_API_KEY_1"))
client_2 = OpenAI(api_key=os.getenv("OPENAI_API_KEY_2"))

# 🧠 AI 역할 프롬프트 (한국어)
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

# 💬 GPT 호출 함수

def chat(client, prompt, history, system_inst):
    msgs = [system_inst] + history + [{"role": "user", "content": prompt}]
    return (
        client.chat.completions.create(
            model="gpt-3.5-turbo", messages=msgs, max_tokens=500
        )
        .choices[0]
        .message.content
    )

# 🧩 Flask API 등록
bp = Blueprint("api", __name__, url_prefix="/api")

# CSV 기반 회사 검색 API
@bp.route("/csv", methods=["GET"])
def csv_search():
    keyword = request.args.get("keyword")
    if not keyword:
        return jsonify({"error": "키워드를 입력하세요"}), 400
    df = load_csv()
    result = search_companies(df, keyword)
    return jsonify({"result": result})

# PDF 요약 API
@bp.route("/pdf", methods=["GET"])
def pdf_summary():
    path = "docs/휴램프로_회사소개서.pdf"
    summary = summarize_pdf(path)
    return jsonify({"result": summary})

# 웹서치 API
@bp.route("/web", methods=["GET"])
def web_search():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "회사명을 입력하세요"}), 400
    info = get_company_info(name)
    return jsonify({"result": info})

# AI 대화 API
@bp.route("/chat", methods=["POST"])
def ai_conversation():
    data = request.get_json()
    prompt = data.get("prompt")
    history = data.get("history", [])
    if not prompt:
        return jsonify({"error": "프롬프트가 없습니다"}), 400

    response = chat(client_1, prompt, history, ai_sales_consultant_instruction)
    return jsonify({"response": response})
