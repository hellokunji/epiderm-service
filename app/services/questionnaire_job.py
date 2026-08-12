import logging

from app.core.flow_log import flow_log
from app.tasks.questionnaire import process_questionnaire_submission

logger = logging.getLogger(__name__)

QUESTIONNAIRE_SUBMITTED_QUEUE = "questionnaire_submitted"


def enqueue_questionnaire_submission(
    *,
    consult_id: str,
    response_id: str,
    patient_id: str,
    category: str,
) -> str:
    """Publish questionnaire submission metadata to the questionnaire_submitted queue."""
    flow_log(
        "04",
        "redis",
        "Publishing task to queue",
        consult_id=consult_id,
        queue=QUESTIONNAIRE_SUBMITTED_QUEUE,
        response_id=response_id,
        patient_id=patient_id,
        category=category,
        task_name="app.tasks.questionnaire.process_submission",
    )
    task = process_questionnaire_submission.apply_async(
        args=[
            {
                "consult_id": consult_id,
                "response_id": response_id,
                "patient_id": patient_id,
                "category": category,
            }
        ],
        queue=QUESTIONNAIRE_SUBMITTED_QUEUE,
    )
    flow_log(
        "04b",
        "redis",
        "Task published to questionnaire_submitted",
        consult_id=consult_id,
        queue=QUESTIONNAIRE_SUBMITTED_QUEUE,
        task_id=task.id,
    )
    return task.id
