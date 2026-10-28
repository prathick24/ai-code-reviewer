from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from services.agent_service import AgentService
from utils.exceptions.error_code import ErrorCode, ErrorCodeStatus
from utils.exceptions.custom_app_exception import CustomAppException
from settings import HttpStatusCode
from models.agent_model import APIResponse, data
from utils.error_logs import log_error
from utils.helper import log_decorator,logger

router = APIRouter(prefix="/MultiAgent/api", tags=["chatbot"])


@router.post("/v1/chatbot")
@log_decorator
async def chatbot_route(
    request: data = Body(...),
):
    try:
        obj = AgentService()
        result = await obj.chatbot_service(
            user_query=request.user_query,
            username=request.username,
        )
        response = APIResponse(data=result, code=HttpStatusCode.OK)
        return JSONResponse(content=response.to_dict(), status_code=HttpStatusCode.OK)

    except CustomAppException:
        raise
    except Exception as e:
        logger.error(str(e))
        log_error("agent_route.py", "chatbot_route()", str(e))
        raise CustomAppException(
            message=f"Router error in chatbot: {str(e)}",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            error_code_id=ErrorCodeStatus[ErrorCode.INTERNAL_SERVER_ERROR],
        )
