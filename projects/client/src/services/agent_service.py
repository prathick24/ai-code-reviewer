from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import SystemMessage, HumanMessage
import json
from settings import HttpStatusCode
from utils.exceptions.error_code import ErrorCode, ErrorCodeStatus
from utils.exceptions.custom_app_exception import CustomAppException
from utils.error_logs import log_error
from utils.helper import get_llm, log_decorator,get_db_uri,logger
from Agents.code_agent import CodeAgent
from Agents.review_agent import ReviewAgent
from Agents.research_agent import ResearchAgent
from Prompts.orchs_prompt import orches_prompt
from langgraph.types import Command
class State(TypedDict, total=False):
   
    user_query: str
    username: str
    decision: str
    AgentPath: str          
    Code: Optional[str]
    ReviewResponse: Optional[dict]
    # IsReviewValid: Optional[bool]
    # NeedsResearch: Optional[bool]  
    ResearchResponse: Optional[str]
    # IsResearchCompleted: Optional[bool]  

class AgentService:



    # def route_by_userquery(self, state: State) -> str:
  
    #     route = state.get("decision", "").strip().lower()
    #     if "research" in route:
    #         return "node_research"
    #     elif "review" in route:
    #         return "node_review"
    #     elif "code" in route:
    #         return "node_code"
    #     else :
    #         return END
    # def route_after_review(self, state: State) -> str:

    #     if state.get("IsReviewValid"):
    #         return END
    #     if state.get("NeedsResearch"):
    #         return "node_research"
    #     return "node_code"

    # def route_after_research(self, state: State) -> str:
    
    #     if state.get("IsResearchCompleted"):
    #         return END
    #     return "node_code" 


    async def node_orchs(self, state: State) -> dict:
  
        llm = get_llm(max_tokens=20, temperature=0)
        messages = [
            SystemMessage(content=orches_prompt),
            HumanMessage(content=state["user_query"]),
        ]
        response = llm.invoke(messages)
        decision:dict = json.loads(response.content)
        if "research" in decision["response"]: 
            path = "node_research"
        elif "review" == decision["response"]:
            path = "node_review"
        elif "code" == decision["response"]:
            path = "node_code"
        else :
            path =decision["response"]

        print(f"[Orchestrator] decision ={decision['response']}")
        return Command(update={"decision":decision["response"], "AgentPath": path},
                       goto=path)
   

    async def node_code_agent(self, state: State) -> dict:
        code = await CodeAgent().create_coder_agent(state)
        
        return Command(update={"Code": code},
                       goto="node_review" )

    async def node_review_agent(self, state: State) -> dict:
        response, valid, needs_research = await ReviewAgent().create_review_agent(state)
        if not valid:
            Goto= "node_code"
        if needs_research:
            Goto= "node_research"
        Goto= END
        return Command(update={
            "ReviewResponse": response
        },
        goto= Goto)

    async def node_researcher_agent(self, state: State) -> dict:
        response, completed = await ResearchAgent().create_research_agent(state)
        if completed:
            Goto= END
        else:
            Goto= "node_code" 
        return Command(update={"ResearchResponse": response},
                       goto= Goto)

  

    @log_decorator
    async def chatbot_service(self, user_query: str, username: str) -> dict:
       
        try:
            graph = StateGraph(State)
            graph.add_node("node_orchs", self.node_orchs)
            graph.add_node("node_code", self.node_code_agent)
            graph.add_node("node_review", self.node_review_agent)
            graph.add_node("node_research", self.node_researcher_agent)

            graph.set_entry_point("node_orchs")

            graph.add_conditional_edges(
                "node_orchs",
                self.route_by_userquery,
                {
                    "node_code": "node_code",
                    "node_review": "node_review",
                    "node_research": "node_research",
                    END:END,
                },
            )

           
            graph.add_edge("node_code", "node_review")

            
           
            graph.add_conditional_edges(
                "node_review",
                self.route_after_review,
                {
                    "node_research": "node_research",
                    "node_code": "node_code",
                    END: END,
                },
            )

   
            graph.add_conditional_edges(
                "node_research",
                self.route_after_research,
                {
                    "node_code": "node_code",
                    END: END,
                },
            )



            async with AsyncPostgresSaver.from_conn_string(get_db_uri()) as checkpointer:
                await checkpointer.setup()
                compiled = graph.compile(checkpointer=checkpointer)
                agent_config = {"configurable": {"thread_id": username}}
                print(f"[AgentService] Compiled graph — thread: {username}")
                data = await compiled.ainvoke(
                    {"user_query": user_query, "username": username},
                    config=agent_config,
                )
              
                
                async for snap in compiled.aget_state_history(agent_config):
                   print(f"  step={snap.metadata['step']}  next={snap.next}  values={snap.values}")
            return {
                "content" : data.get("decision"),
                "code": data.get("Code"),
                "review_response": data.get("ReviewResponse"),
                "research_response": data.get("ResearchResponse"),
            }

        except CustomAppException:
            raise
        except Exception as e:
            logger.error(str(e))
            log_error("agent_service.py", "chatbot_service()", str(e))
            raise CustomAppException(
                message=f"Service error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
                error_code_id=ErrorCodeStatus[ErrorCode.INTERNAL_SERVER_ERROR],
            )
