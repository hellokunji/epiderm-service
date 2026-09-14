import logging

from bson import ObjectId
from bson.errors import InvalidId

from app.core.celery_app import celery_app
from app.core.flow_log import flow_log
from app.core.mongodb import connect_to_mongo, get_mongo_db
from app.models.consult import ConsultStatus
from app.services.consult import update_consult_status
from app.services.diagnosis_job import enqueue_diagnosis_for_response
from app.services.questionnaire_response import COLLECTION_NAME

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.questionnaire.process_submission",
    max_retries=3,
    default_retry_delay=15,
)
def process_questionnaire_submission(self, payload: dict) -> dict:
    """Consume questionnaire submission, then hand off to the AI diagnosis worker."""
    consult_id = payload["consult_id"]
    response_id = payload["response_id"]
    patient_id = payload["patient_id"]
    category = payload["category"]

    flow_log(
        "06",
        "consumer",
        "Pulled task from questionnaire_submitted queue",
        consult_id=consult_id,
        queue="questionnaire_submitted",
        task_id=self.request.id,
        response_id=response_id,
        patient_id=patient_id,
        category=category,
    )

    connect_to_mongo()
    mongo_db = get_mongo_db()

    try:
        document = mongo_db[COLLECTION_NAME].find_one({"_id": ObjectId(response_id)})
    except InvalidId as exc:
        flow_log(
            "07",
            "consumer",
            "Invalid response_id — cannot load Mongo document",
            consult_id=consult_id,
            response_id=response_id,
        )
        raise ValueError(f"Invalid response_id: {response_id}") from exc

    if document is None:
        flow_log(
            "07",
            "consumer",
            "Mongo document not found — will retry",
            consult_id=consult_id,
            response_id=response_id,
            retry=self.request.retries,
        )
        raise self.retry(exc=ValueError(f"Response not found: {response_id}"))

    has_questionnaire = document.get("questionnaire") is not None
    image_count = len(document.get("images") or [])
    flow_log(
        "07",
        "mongodb",
        "Loaded questionnaire_response for processing",
        consult_id=consult_id,
        response_id=response_id,
        has_questionnaire=has_questionnaire,
        image_count=image_count,
    )

    flow_log(
        "07b",
        "consumer",
        "Setting consult status to DRAI_DG_PROCESSING",
        consult_id=consult_id,
    )
    update_consult_status(consult_id, ConsultStatus.DRAI_DG_PROCESSING)

    diagnosis_job = enqueue_diagnosis_for_response(
        consult_id=consult_id,
        response_id=response_id,
        patient_id=patient_id,
        questionnaire=document.get("questionnaire"),
        images=document.get("images"),
        category=category,
    )

    diagnosis_job_id = diagnosis_job.job_id if diagnosis_job else None
    if diagnosis_job_id:
        mongo_db[COLLECTION_NAME].update_one(
            {"_id": ObjectId(response_id)},
            {"$set": {"diagnosis_job_id": diagnosis_job_id}},
        )
        flow_log(
            "09",
            "mongodb",
            "Linked diagnosis_job_id on questionnaire_response",
            consult_id=consult_id,
            response_id=response_id,
            diagnosis_job_id=diagnosis_job_id,
        )
        flow_log(
            "10",
            "consumer",
            "Hand-off complete — waiting on diagnosis worker",
            consult_id=consult_id,
            diagnosis_job_id=diagnosis_job_id,
            queue=diagnosis_job.queue,
        )
    else:
        flow_log(
            "08",
            "consumer",
            "Skipped diagnosis enqueue — no questionnaire or images",
            consult_id=consult_id,
            response_id=response_id,
        )

    return {
        "consult_id": consult_id,
        "response_id": response_id,
        "patient_id": patient_id,
        "category": category,
        "has_questionnaire": has_questionnaire,
        "image_count": image_count,
        "diagnosis_job_id": diagnosis_job_id,
        "status": "handed_off_to_diagnosis" if diagnosis_job_id else "skipped_diagnosis",
    }
