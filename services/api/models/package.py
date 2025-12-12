"""
Pydantic models for package ingestion.
"""

from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PackageStatus(str, Enum):
    """Package processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    PARSED = "parsed"
    GEOCODED = "geocoded"
    ROUTED = "routed"
    DELIVERED = "delivered"
    FAILED = "failed"
    VERIFICATION_NEEDED = "verification_needed"


class GPSLocation(BaseModel):
    """GPS coordinates."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class PackageIngestRequest(BaseModel):
    """Request model for OCR text ingestion from device."""
    
    device_id: str = Field(..., min_length=1, max_length=50, description="Device identifier")
    package_id: str = Field(..., min_length=1, max_length=50, description="Package identifier")
    ocr_text: str = Field(..., min_length=1, description="OCR-extracted text from label")
    ocr_confidence: float = Field(..., ge=0, le=1, description="OCR confidence score (0-1)")
    timestamp: Optional[datetime] = Field(default=None, description="Capture timestamp")
    gps: Optional[GPSLocation] = Field(default=None, description="Device GPS location")
    priority: str = Field(default="standard", pattern="^(urgent|high|standard|low)$")
    operator_id: Optional[str] = Field(default=None, max_length=50)
    image_id: Optional[str] = Field(default=None, max_length=100)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "device_id": "scanner-17",
                    "package_id": "PKT2025123456",
                    "ocr_text": "Jalan Merdeka 45 Rt 02 Rw 03, Kebayoran Lama, Jakarta Selatan 12220",
                    "ocr_confidence": 0.72,
                    "gps": {"lat": -6.225, "lon": 106.795},
                    "priority": "standard"
                }
            ]
        }
    }


class ImageIngestRequest(BaseModel):
    """Request model for image ingestion (server-side OCR)."""
    
    device_id: str = Field(..., min_length=1, max_length=50)
    package_id: str = Field(..., min_length=1, max_length=50)
    timestamp: Optional[datetime] = Field(default=None)
    gps: Optional[GPSLocation] = Field(default=None)
    priority: str = Field(default="standard", pattern="^(urgent|high|standard|low)$")
    operator_id: Optional[str] = Field(default=None, max_length=50)


class PackageIngestResponse(BaseModel):
    """Response model for package ingestion."""
    
    id: str = Field(..., description="Internal package UUID")
    package_id: str = Field(..., description="External package identifier")
    status: PackageStatus = Field(..., description="Current processing status")
    message: str = Field(..., description="Status message")
    created_at: str = Field(..., description="Creation timestamp")
    parsed_address: Optional[dict] = Field(default=None, description="Parsed address if available")
    geocoded: bool = Field(default=False, description="Whether address was geocoded")
    requires_verification: bool = Field(default=False, description="Needs human verification")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "package_id": "PKT2025123456",
                    "status": "parsed",
                    "message": "Package ingested and address parsed successfully",
                    "created_at": "2025-12-12T08:23:45Z",
                    "parsed_address": {
                        "street": "Jalan Merdeka",
                        "house_number": "45",
                        "rt": "02",
                        "rw": "03",
                        "subdistrict": "Kebayoran Lama",
                        "city": "Jakarta Selatan",
                        "postal_code": "12220"
                    },
                    "geocoded": True,
                    "requires_verification": False
                }
            ]
        }
    }
