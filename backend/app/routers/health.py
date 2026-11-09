from fastapi import APIRouter, Depends

from app.dependencies import get_llm
from app.providers.llm import LLMProvider

router = APIRouter(tags=["saúde"])


@router.get("/health")
def health(llm: LLMProvider = Depends(get_llm)):
    return {"status": "ok", "modo": llm.modo, "versao": "1.0.0"}
