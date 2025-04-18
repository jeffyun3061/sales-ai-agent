# --- [환경 설정 안내: UnstructuredPDFLoader 사용 시] ---
# 필수 설치 패키지 (requirements.txt에 포함 필요):
# pip install unstructured langchain langchain-community pdf2image pytesseract python-dotenv

# Windows 환경일 경우 추가 설정 (libmagic 관련 오류 방지):
# pip uninstall python-magic
# pip install python-magic-bin

# 의존 라이브러리 설치 (시스템 환경에 따라 필요):
# - Poppler (pdf2image 용): https://blog.alivate.com.au/poppler-windows/ 참고 (Windows)
#   → 설치 후 poppler/bin 경로를 시스템 PATH에 추가
# - Tesseract OCR: https://github.com/tesseract-ocr/tesseract
#   → 설치 후 시스템 환경변수 TESSDATA_PREFIX 설정 (예: C:/Program Files/Tesseract-OCR/tessdata)


from langchain_community.document_loaders import UnstructuredPDFLoader
from openai import OpenAI
import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
import base64
from io import BytesIO

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
images = [] # 회사 pdf에서 구성도 등의 이미지나 표도 요약에 사용하기 위해 만든 리스트

# tesseract 데이터 경로 지정
file_name = "(주)셀리즈 사업계획서(IR Deck)_v1.3.pdf"
pdf = UnstructuredPDFLoader(
    file_name,
    mode="elements",
    strategy="hi_res",
    extract_tables=True,
    infer_table_structure=True,
    ocr_languages="eng+kor"
)

try:
    documents = pdf.load()
    print(f"문서 개수: {len(documents)}")
    if not documents:
        print("문서를 불러오지 못했어요. 아무것도 추출되지 않았습니다.")
    for i, doc in enumerate(documents):
        print(f"\n[Doc {i+1}] type: {doc.type}")
        print(doc.metadata)
        print(doc.page_content[:300] if hasattr(doc, 'page_content') and doc.page_content else "(본문 없음)")

except Exception as e:
    print("오류 발생:", e)


doc = "\n".join([doc.page_content for doc in documents])

#이미지로 변환
pages = convert_from_path(file_name, dpi=300)
총_페이지=len(pages)

for doc in documents:
    if "coordinates" in doc.metadata and "points" in doc.metadata["coordinates"]:
        x1,y1,x2,y2 = doc.metadata["coordinates"]["points"]
        page = pages[doc.metadata["page_number"] - 1]

        #좌표 기반 이미지 크롭
        cropped = page.crop((x1[0], x1[1], x2[0], x2[1]))

        #이미지 base64로 변환
        buffer = BytesIO()
        cropped.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        image_url = f"data:image/png;base64,{img_str}"
        images.append(image_url)


# ___________ 회사 정보 요약을 위한  LLM__________________
# 1. 모델 초기화
client= OpenAI(api_key=api_key)

# 2. 프롬프트 템플릿 정의
contents = [{"type": "text", "text": f"회사소개서{documents}와 회사 소개서에 있던 이미지를 분석해서 회사 정보를 제공 서비스와 해결하는 문제를 중심으로 정리해주세요."}] # 지침

# pdf에 모든 이미지도 LLM에 삽입하기 위한 반복문
for img in images:
    contents.append({"type": "image_url", "image_url": {"url": img}})
# 3. 응답 생성
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": contents}
    ],
    temperature=0
)

# 4. 응답 마크다운으로 저장
result = response.choices[0].message.content
filename = f"summary_{file_name.replace('.pdf', '')}.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(result)
print()
print("____________________________________________")
print(result) 

# ______________________________________________________