from typing import Any

from fastapi import APIRouter, HTTPException

from api.schemas import ChatRequest, ChatResponse
from config.setting import load_agent_capabilities


def create_router(agent_provider: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health_check():
        print(agent_provider.api_key)
        return {"status": "ok"}

    @router.get("/capabilities")
    def capabilities() -> dict[str, Any]:
        """返回调试后台用于点亮或置灰面板的能力声明。"""

        # capabilities 只服务调试后台能力开关，不参与 `/chat` 的业务判断。
        return load_agent_capabilities()

    @router.post("/chat")
    def chat(chat_request: ChatRequest) -> ChatResponse:
        try:
            return agent_provider().chat(chat_request)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e

    return router
