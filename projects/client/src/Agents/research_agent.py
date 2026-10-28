from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import create_react_agent
from settings import config, HttpStatusCode
from utils.exceptions.error_code import ErrorCode, ErrorCodeStatus
from utils.exceptions.custom_app_exception import CustomAppException
from utils.error_logs import log_error
from utils.helper import get_llm, log_decorator,get_db_uri,logger
from Prompts.research_prompt import research_system_prompt
from models.agent_model import Research
from langchain.agents import create_agent
from langchain.messages import HumanMessage,SystemMessage
class ResearchAgent:
    @log_decorator
    async def create_research_agent(self, state) -> tuple[str, bool]:

        try:
            llm = get_llm(max_tokens=500, temperature=0.3)
    
            # Enrich query with code + review context when research was triggered by a review failure
            user_query = state["user_query"]
            if state.get("Code") and state.get("ReviewResponse"):
                user_query = (
                    f"{user_query}\n\n"
                    f"Code that was reviewed:\n{state['Code']}\n\n"
                    f"Review feedback requiring research:\n{state['ReviewResponse']}\n\n"
                    f"Please research the topic to provide context for improving this code."
                )

            agent = create_agent(
                model=llm,
                tools=[],
                system_prompt=SystemMessage(content=research_system_prompt),
                response_format=Research,
      
            )
  
            data = await agent.ainvoke(
                {"messages": HumanMessage(content = user_query)},
            )

            result = data["structured_response"]
            print(result)
            print(f"[ResearchAgent] IsResearchCompleted={result.IsResearchCompleted}")
            return result.ResearchResponse, result.IsResearchCompleted

        except CustomAppException:
            raise
        except Exception as e:
            logger.error(str(e))
            log_error("research_agent.py", "create_research_agent()", str(e))
            raise CustomAppException(
                message=f"Research agent error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
                error_code_id=ErrorCodeStatus[ErrorCode.INTERNAL_SERVER_ERROR],
            )
