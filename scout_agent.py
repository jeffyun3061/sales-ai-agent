import os
from dotenv import load_dotenv
from typing import Annotated, Dict, List, TypedDict, Any, Optional

from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_community.tools.tavily_search import TavilySearchResults

from kiwipiepy import Kiwi

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

kiwi = Kiwi()

# kiwi 토크나이징 함수
def kiwi_tokenize(text: str) -> List[str]:
    """
    Tokenizes the input text using the Kiwi tokenizer.
    """
    tokens = kiwi.tokenize(text)
    return [token.form for token in tokens if token.tag != "SPACE"]

# 상태
class GraphState(TypedDict):
    """
    Represents the state of the graph.
    """
    query: str
    documents: Document
    web_results: List[Document]
    answer: Optional[str]
    message: Optional[str]
    

# 샘플 문서
sample_documents = [
    Document(page_content="회사 이름 : A ", metadata={"source": "sample1"}),
    Document(page_content="회사 소개 : 판매를 위한 영업 회사 ", metadata={"source": "sample2"}),
]

# 리트리버 정의
# 1. BM25 리트리버
bm25_retriever = BM25Retriever.from_documents(
    documents=sample_documents,
    search_kwargs={"k": 5},
    tokenizer=kiwi_tokenize,
)
# 2. FAISS 리트리버
faiss_retriever = FAISS.from_documents(
    documents=sample_documents,
    embedding=embedding  
).as_retriever(search_kwargs={"k": 5})

# 3. Ensemble 리트리버
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever],
    weights=[0.5, 0.5], # 추후 비율 조정
)
# 4. Tavily 리트리버
tavily_search = TavilySearchResults(max_results=5)

#LLM
llm = ChatOpenAI(temperature=0)

# 노드 정의
def retrieve_documents(state: GraphState) -> Dict:
    "문서를 검색하는 노드입니다."
    query = state["query"]
    docs = ensemble_retriever.invoke(query)
    return {"documents": docs}

def check_document_relevance(state: GraphState) -> Dict:
    "검색된 문서의 relevance를 체크하는 노드입니다."
    # relevance 체크 로직
    query = state["query"]
    docs = state["documents"]

    context = "n\n".join([doc.page_content for doc in docs])

    # relevance 체크 프롬프트
    prompt_template = f"""
        "다음 문서들이 주어졌을 때, 이 문서들이 질문에 대한 답변으로 적절한지 판단하세요.\n"
        "질문: {query}\n"
        "문서들: {context}\n"
        문서가 질문에 관련이 있으면 yes, 아니면 no로 대답하세요.\n
    """

    # 관련성 확인
    response = llm.invoke(prompt_template)
    relevance = "yes" if "yes" in response.content.lower() else "no"

    return {"relevance": relevance}

def web_serch(state: GraphState) -> Dict:
    "웹 검색을 수행하는 노드입니다."
    query = state["query"]
    search_results = tavily_search.invoke(query)
    return {"search_results": search_results}

def generate_anser(state: GraphState) -> Dict:
    "답변을 생성하는 노드입니다."
    query = state["query"]

    # 문서 또는 웹 검색 결과 사용하기
    if "web_results" in state and state["web_results"]:
        context = "\n\n".join(state["web_results"])
        sorce = "web"
    else:
        context = "\n\n".join(doc.page_content for doc in state["documents"])
        sorce = "document"

    # 답변 생성 프롬프트
    prompt_template = f"""
        "질문: {query}\n"
        "문서: {context}\n"
        "이 문서들을 바탕으로 질문에 대한 답변을 생성하세요.\n
        "답변 소스: {sorce}\n
    """

    # 답변 생성
    response = llm.invoke(prompt_template)
    answer = response.content

    # 메시지 추가
    messages = state.get("messages", [])
    messages.append(HumanMessage(content=query))
    messages.append(AIMessage(content=answer))

    return {
        "answer": answer,
        "messages": messages,
    }

# 라우터 함수
def route_by_relevance(state: GraphState) -> str:
    """
    Determines the next node to execute based on the current state.
    """
    if "relevance" in state and state["relevance"] == "yes":
        return "generate_answer"
    else:
        return "web_search"
    
# 그래프 정의
workflow = StateGraph(GraphState)

# 노드 추가
workflow.add_node("retrieve_documents", retrieve_documents)
workflow.add_node("check_document_relevance", check_document_relevance)
workflow.add_node("web_search", web_serch)
workflow.add_node("generate_answer", generate_anser)

# 엣지 추가
workflow.add_edge("retrieve_documents", "check_document_relevance")
workflow.add_conditional_edges(
    "check_document_relevance",
    route_by_relevance,
    {
        "generate_answer": "generate_answer",
        "web_search": "web_search"
    }
)
workflow.add_edge("web_search", "generate_answer")
workflow.add_edge("generate_answer", END)

# 시작점
workflow.set_entry_point("retrieve_documents")

# 체크 포인터
memory = MemorySaver()

# 그래프 컴파일
app = workflow.compile(checkpointer=memory)

# 실행 함수
def process_query(query: str) -> Dict:
    """
    Processes the input query and returns the final answer.
    """
    config = RunnableConfig(recursion_limit=10,configurable={"thread_id": "unique_thread_id"})
    inputs = GraphState(query=query, documents=[])
    result =  app.invoke(inputs, config)
    return result

# 테스트
if __name__ == "__main__":
    query = "예시 질문 : 내 회사 정보에 맞게 리드 리스트를 만들어줘"
    result = process_query(query)
    print(f"질문 : {result['query']}")
    print(f"답변 : {result['answer']}")
    #print(f"문서 : {result['document']}")
    #print(f"웹 결과 : {result['web_results']}")