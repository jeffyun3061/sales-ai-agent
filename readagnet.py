from agents import Agent, WebSearchTool, Runner
from agents.tool import UserLocation
import os
from dotenv import load_dotenv
import nest_asyncio
from langgraph.graph import StateGraph
from typing import TypedDict

class LeadScoutState(TypedDict):
    question: str
    scout_result: str

graph = StateGraph(LeadScoutState) # LangGraph의 그래프 인스턴스 생성
SECRET_ENV = os.getenv("OPENAI_API_KEY")
load_dotenv()
nest_asyncio.apply()

Current_Status = {} # 에이전트가 실행되면서 그 안에 데이터를 채워 넣고, 그 상태값을 기반으로 다음 노드를 결정하기 위한 딕셔너리

def agent_node(state: dict) -> dict:

    agent = Agent(
        name = " Assistant",
        instructions=(
            "You are a Lead Scout specialized in identifying potential leads and gathering initial data."
            "When searching for leads, explore company databases, websites, social media, and industry events."
            "Provide insights on company name, size, industry, recent activities, and contact information."
            "Ensure your findings are relevant, accurate, and well-organized."
        ),
        tools = [
            WebSearchTool(
                user_location=UserLocation(
                    type="approximate",
                    city="Seoul"
                    )
                )
            ],
        model="gpt-4o"
    )
    question = "최근에 주목할 만한 새로운 스타트업들의 목록을 제공해 주실 수 있나요?" # 현재는 테스트 용 추후 LangGraph 완성 시 질문을 상태로 받아 처리하는 방식 등으로 변경 필요
    result = Runner.run_sync(agent, question)
    print(result.final_output)
    return {"scout_result" : result.final_output }

graph.add_node("Assistant", agent_node)

graph.set_entry_point("Assistant")

app = graph.compile()

result = app.invoke(Current_Status)