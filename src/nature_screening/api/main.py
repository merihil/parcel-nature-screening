from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from nature_screening.analysis.analysis import analyze_parcel
from nature_screening.analysis.parcel_lookup import get_parcel_by_property_id
from nature_screening.etl.ensure_coverage import (
    ensure_forest_stand_coverage,
    ensure_parcel_exists,
    ensure_special_habitat_coverage,
)

app = FastAPI(title="Parcel Nature Screening API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/parcels/{property_id}")
def get_parcel(property_id: str):
    parcel = get_parcel_by_property_id(property_id)

    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    return parcel


@app.get("/parcels/{property_id}/analysis")
def get_parcel_analysis(property_id: str):
    ensure_parcel_exists(property_id)

    parcel = get_parcel_by_property_id(property_id)

    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    ensure_forest_stand_coverage(property_id)
    ensure_special_habitat_coverage(property_id)

    return analyze_parcel(property_id)


# Mounted last so it never shadows the API routes above — Starlette matches
# routes in registration order, and this is a catch-all at "/".
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
