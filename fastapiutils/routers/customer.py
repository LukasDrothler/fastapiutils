from fastapi import APIRouter, Depends, HTTPException, Path, Request

from ..models import CreateCancellation, CreateFeedback
from ..database_service import DatabaseService
from ..i18n_service import I18nService
from ..customer_form_service import CustomerFormService
from ..dependencies import CurrentAdminUser, get_customer_form_service, get_database_service, get_i18n_service

import logging

logger = logging.getLogger('uvicorn.error')

"""Create customer form management router"""
router = APIRouter()

@router.get("/forms/cancellation", tags=["forms"])
def get_cancellation(
    request: Request,
    current_admin: CurrentAdminUser,
    customer_service: CustomerFormService = Depends(get_customer_form_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    ):
    """Get all cancellations"""
    locale = i18n_service.extract_locale_from_request(request)
    if not current_admin.is_admin:
        raise HTTPException(status_code=403)
    return customer_service.get_cancellations(
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
        )


@router.post("/forms/cancellation", tags=["forms"], status_code=201)
def insert_cancellation(
    cancellation_data: CreateCancellation,
    request: Request,
    customer_service: CustomerFormService = Depends(get_customer_form_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service)
    ):
    """Insert a new cancellation"""
    locale = i18n_service.extract_locale_from_request(request)
    return customer_service.create_cancellation(
        cancellation_data=cancellation_data,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
        )


@router.patch("/forms/cancellation/{cancellation_id}/archive", tags=["forms"], status_code=201)
def archive_cancellation(
    request: Request,
    current_admin: CurrentAdminUser,
    customer_service: CustomerFormService = Depends(get_customer_form_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    cancellation_id: int = Path(description="The ID of the cancellation to archive")
    ):
    """Archive a cancellation by its ID"""
    locale = i18n_service.extract_locale_from_request(request)
    if not current_admin.is_admin:
        raise HTTPException(status_code=403)
    return customer_service.archive_cancellation(
        cancellation_id=cancellation_id,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
    )


@router.get("/forms/feedback", tags=["forms"])
def get_feedback(
    request: Request,
    current_admin: CurrentAdminUser,
    customer_service: CustomerFormService = Depends(get_customer_form_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service)
    ):
    """Get all feedback"""
    locale = i18n_service.extract_locale_from_request(request)
    if not current_admin.is_admin:
        raise HTTPException(status_code=403)
    return customer_service.get_feedbacks(
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
        )


@router.post("/forms/feedback", tags=["forms"], status_code=201)
def insert_feedback(
    feedback_data: CreateFeedback,
    request: Request,
    customer_service: CustomerFormService = Depends(get_customer_form_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service)
    ):
    """Insert a new feedback"""
    locale = i18n_service.extract_locale_from_request(request)
    return customer_service.create_feedback(
        feedback_data=feedback_data,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
    )

@router.patch("/forms/feedback/{feedback_id}/archive", tags=["forms"], status_code=201)
def archive_feedback(
    request: Request,
    current_admin: CurrentAdminUser,
    customer_service: CustomerFormService = Depends(get_customer_form_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    feedback_id: int = Path(description="The ID of the feedback to archive")
    ):
    """Archive a feedback by its ID"""
    locale = i18n_service.extract_locale_from_request(request)
    if not current_admin.is_admin:
        raise HTTPException(status_code=403)
    return customer_service.archive_feedback(
        feedback_id=feedback_id,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
    )
