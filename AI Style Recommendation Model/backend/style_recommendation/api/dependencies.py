"""Override these dependencies in tests to replace workflow services."""
from fastapi import Depends, Request


def get_resources(request: Request):
    return request.app.state.resources


def get_recommendation_pipeline(resources=Depends(get_resources)):
    return resources.pipeline


def get_requirement_service(resources=Depends(get_resources)):
    return resources.requirements


def get_stylist_service(resources=Depends(get_resources)):
    return resources.stylist


def get_catalog(resources=Depends(get_resources)):
    return resources.catalog
