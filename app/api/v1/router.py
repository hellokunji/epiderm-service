from fastapi import APIRouter, Depends

from app.api.v1.endpoints import consult, diagnosis, kit, prescription, questionnaire, llm

from app.api.deps.auth import get_current_user, verify_s2s_api_key

# Public Router
public_router = APIRouter()

# Client Router
api_router = APIRouter(dependencies=[Depends(get_current_user)])
api_router.include_router(questionnaire.api_router, prefix="/questionnaire")
api_router.include_router(prescription.api_router, prefix="/prescription")
api_router.include_router(diagnosis.api_router, prefix="/diagnosis")
api_router.include_router(consult.api_router, prefix="/consult")
api_router.include_router(kit.api_router, prefix="/kit")
api_router.include_router(llm.api_router, prefix="/llm")

# S2S Router
s2s_router = APIRouter(dependencies=[Depends(verify_s2s_api_key)])
s2s_router.include_router(questionnaire.s2s_router, prefix="/questionnaire")
s2s_router.include_router(llm.s2s_router, prefix="/llm")
s2s_router.include_router(diagnosis.s2s_router, prefix="/diagnosis")

router = APIRouter()
router.include_router(api_router, prefix="", tags=["Client"])
router.include_router(s2s_router, prefix="/internal", tags=["S2S"])
router.include_router(public_router, prefix="/public", tags=["Public"])