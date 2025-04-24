🧠 AI-to-AI Sales Conversation Simulator

GPT 기반의 AI 세일즈 컨설턴트와 바이어 역할 에이전트가
실시간으로 대화하는 AI-to-AI 시뮬레이션 플랫폼입니다.

🚀 프로젝트 구성

ai-to-ai-demo/
├── backend/
│   ├── app.py                 # Flask 애플리케이션 진입점
│   ├── peak_agent_conversation.py  # CLI 기반 AI 시뮬레이터
│   ├── routes.py              # API 라우팅 (Blueprint)
│   ├── utils/ or peak/        # csv/pdf/web 유틸리티
│   ├── data/                  # company_data.csv
│   ├── docs/                  # 회사소개서 PDF
│   └── .env                   # OpenAI API Key
│
├── frontend/
│   ├── src/App.js             # React 기반 UI (axios 연동)
│   └── package.json

🎯 핵심 기능

모드	설명
🟡 CSV 기반 대화	CSV로부터 회사명/업종/연락처 추출 → 세일즈 대화 생성

🔵 PDF 기반 대화	회사소개서(PDF) 텍스트 요약 → 대화 주제 자동 생성

🟢 웹검색 기반 대화	DuckDuckGo 웹 검색 → 회사 정보 추출 후 대화 진행

⚪ Custom	사용자가 직접 대화 주제 입력 후 AI 간 대화

💬 대화 구조

GPT-3.5 기반 Sales Consultant ↔ Buyer AI가 5턴 대화

각각의 역할에 맞는 system prompt 세팅

실시간 응답 생성 및 콘솔 출력 또는 API 응답(JSON)

🔧 실행 방법

📌 1. CLI 시뮬레이터 실행

cd backend
python peak_agent_conversation.py

📌 2. Flask API 실행

cd backend
python app.py
Swagger 문서 연동 예정

API 목록

POST /api/chat

GET /api/csv

GET /api/pdf

GET /api/web

📌 3. React UI 실행

cd frontend
npm install
npm start
모드 선택 드롭다운 + 프롬프트 입력 → 실시간 응답 확인 가능

📦 설치 패키지 (requirements.txt)

openai
flask
python-dotenv
pandas
PyPDF2
duckduckgo-search
beautifulsoup4
requests

⚙️ 진행 중
 대화 기록 히스토리 API화

 Swagger 문서 자동 생성

 SDK 패키징 (csv/pdf/web 추출 기능 분리)

 실제 Spring 서버와의 API 연동 준비

📌 사용 목적
사내 AI 기반 세일즈 자동화 기획안의 시연/실험용

내부에서 AI의 대화 능력을 실제 데이터 기반으로 검증

향후 B2B SaaS 형태 SDK/API화 가능성 타진

