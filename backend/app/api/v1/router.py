"""CAIP-Karnataka — API v1 Router Aggregator"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, districts, intelligence, etl

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(districts.router)
api_router.include_router(intelligence.router)
api_router.include_router(etl.router, prefix="/etl")
