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
import base64
from io import BytesIO


load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
images = [] # 회사 pdf에서 구성도 등의 이미지나 표도 요약에 사용하기 위해 만든 리스트

# tesseract 데이터 경로 지정
file_name = "(주)두뇌로세계로_연구개발계획서(R&D바우처-융합촉진형).pdf"

# PDF를 구성요소별(텍스트, 이미지, 표 등)로 로드
pdf = UnstructuredPDFLoader(
    file_name,
    mode="elements", # PDF를 구성 요소 단위로 분리하여 로딩 (텍스트, 이미지, 표 등으로 구분됨)
    strategy="hi_res", # 고해상도 OCR 추출 및 좌표 기반 추출을 수행
    extract_tables=True, # 표(Table)를 인식하여 추출
    infer_table_structure=True, # 표의 구조(행/열/셀)를 추론하여 정돈된 형태로 반환
    ocr_languages="eng+kor" # OCR에 사용할 언어 (영어 + 한국어)
)

# PDF 문서 로드 및 요소 추출
documents = pdf.load()


# pdf에서 추출한 텍스트 하나로 합치기
doc = "\n".join([doc.page_content for doc in documents])

#_________________PDF 이미지 영역 추출 및 필터링_______________________________________________________________________
pages = convert_from_path(file_name, dpi=300) # PDF 페이지를 이미지 리스트로 변환

for doc in documents:
    if ("coordinates" in doc.metadata and 
        "points" in doc.metadata["coordinates"]):
        
        # 이미지 영역 좌표 정보 추출
        x1,y1 = doc.metadata["coordinates"]["points"][0]
        x2, y2 = doc.metadata["coordinates"]["points"][2]
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        area = width * height
        layout_width = doc.metadata.get("layout_width")
        layout_height = doc.metadata.get("layout_height")     

        # 의미 있는 이미지로 판단되는 조건 (OCR 텍스트, 키워드, 크기 비율 기준)
        if (doc.metadata.get("category") == "Image" and 
            (len(doc.page_content) > 30  or 
            any(kw in doc.page_content for kw in ["시스템", "프로세스", "플로우", "구성", "구조"]) or 
            (layout_width is not None and layout_height is not None and (area / (layout_width * layout_height))) > 0.1)):

            page = pages[doc.metadata["page_number"] - 1] # 이미지 크롭할 페이지

            # 이미지 영역 잘라내고, 리사이징 후 흑백 변환 후 압축
            cropped = page.crop((x1, y1, x2, y2))
            small = cropped.resize((cropped.width // 2, cropped.height // 2))
            gray = small.convert("L")

            #이미지 base64로 변환
            buffer = BytesIO()
            gray.save(buffer, format="JPEG", quality=50)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            image_url = f"data:image/png;base64,{img_str}"
            images.append(image_url)

print("image의 총 개수", len(images))
#_________________________________________________________________________________________________


# ___________회사 정보 요약을 위한  LLM__________________
# 1. 모델 초기화
print("회사정보 요약 시작")
client= OpenAI(api_key=api_key)

# 2. 프롬프트 템플릿 정의
contents = [{"type": "text",
"text": f"""
다음은 회사 소개서에서 추출한 텍스트와 이미지입니다.
텍스트와 이미지를 참고하여 회사의 문제점, 솔루션, 비즈니스 모델, 시장 목표, 팀 구성, 차별화 포인트를 자세히 요약해 주세요.
텍스트:
{doc}
"""}
] # 지침

# LLM에 이미지 정보 추가
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

# 4. 응답 생성 후 마크다운으로 저장
result = response.choices[0].message.content
filename = f"summary_{file_name.replace('.pdf', '')}.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(result)
print()
print("____________________________________________")
print(result) 

# ______________________________________________________