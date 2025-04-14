from agents import Agent, WebSearchTool, Runner, function_tool
from agents.tool import UserLocation
import os
from dotenv import load_dotenv
import nest_asyncio
from langgraph.graph import StateGraph
from typing import TypedDict, List, Optional, Any
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.tools import BaseTool
from kiwipiepy import Kiwi
from langchain_openai import OpenAIEmbeddings


kiwi = Kiwi()
embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

# kiwi 토크나이징 함수
def kiwi_tokenize(text: str) -> List[str]:
    """
    Tokenizes the input text using the Kiwi tokenizer.
    """
    tokens = kiwi.tokenize(text)
    return [token.form for token in tokens if token.tag != "SPACE"]

class LeadScoutState(TypedDict):
    question: str
    scout_result: str

graph = StateGraph(LeadScoutState) # LangGraph의 그래프 인스턴스 생성
SECRET_ENV = os.getenv("OPENAI_API_KEY")
load_dotenv()
nest_asyncio.apply()

question = "2024년 가장 주목받는 AI 스타트업은?" # 현재는 테스트 용 추후 모든 에이전트 완성 후 LangGraph 완성 시 질문을 상태로 받아 처리하는 방식 등으로 변경 필요
Current_Status = {"question": question} # 에이전트가 실행되면서 그 안에 데이터를 채워 넣고, 그 상태값을 기반으로 다음 노드를 결정하기 위한 딕셔너리


@function_tool # 문서 검색 툴
def  CustomFileSearchTool():
    print(" CustomFileSearchTool 실행됨")
    Company_data = CSVLoader(file_path="company_data.csv", encoding='UTF8')
    Company_data_documents = Company_data.load()

    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000, # 한 번에 처리할 텍스트 크기
        chunk_overlap= 100, # 분할된 텍스트 간 겹치는 부분의 크기
    )

    splits = recursive_text_splitter.split_documents(Company_data_documents)

    # 리트리버 정의
    # 1. BM25 리트리버
    bm25_retriever = BM25Retriever.from_documents(
        documents=splits,
        search_kwargs={"k": 5},
        tokenizer=kiwi_tokenize,
    )

    if os.path.exists("vector_index/index.faiss") and os.path.exists("vector_index/index.pkl") : # 경로에 저장한 벡터 인덱스가 있는 경우
        faiss_retriever = FAISS.load_local("vector_index", embedding, allow_dangerous_deserialization=True).as_retriever(search_kwargs={"k": 5})
    else: # 없는 경우
        # 2. FAISS 리트리버
        faiss_retriever = FAISS.from_documents(
            documents=splits,
            embedding=embedding  
        ).as_retriever(search_kwargs={"k": 5})

    # 3. Ensemble 리트리버
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.5, 0.5], # 추후 비율 조정
    )

    results = ensemble_retriever.invoke(question)
    if not results:
        return "검색된 결과가 없습니다."
    # 2. 문서 리스트 반환 (또는 문자열 변환)
    return "\n\n".join(doc.page_content for doc in results)


def agent_node(state: dict) -> dict:
    question : str = state["question"]
    agent = Agent(
        name = " Assistant",
        instructions=(
            "You are a Lead Scout AI Agent responsible for identifying promising companies and gathering accurate lead information.\n\n"
            "Your main sources include:\n"
            "- Internal company database (CSV-based)\n"
            "- Public websites and news articles (via WebSearchTool)\n\n"
            
            "When answering a query:\n"
            "- If the user question includes specific conditions like location or industry, search the internal CSV database first.\n"
            "- If the user is asking for recent trends or newly emerging startups, use the WebSearchTool.\n"
            
            "For each lead you report, include:\n"
            "- Company name, industry, address, executive, homepage, contact number, created_at, updated_at, sales, and total funding.\n\n"
            "Ensure the response is clear, structured, and based on available data only. Avoid hallucination.\n"
        ),
        tools = [
            WebSearchTool(
                user_location=UserLocation(
                    type="approximate",
                    city="Seoul"
                    )
                ),
            CustomFileSearchTool,
            ],
        model="gpt-4o"
    )

    result = Runner.run_sync(agent, question)
    print(result.final_output)
    return {"scout_result" : result.final_output }

graph.add_node("Assistant", agent_node)

graph.set_entry_point("Assistant")

app = graph.compile()

result = app.invoke(Current_Status)