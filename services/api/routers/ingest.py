"""
Ingest API endpoints.
Handles OCR text and image ingestion from edge devices.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.repositories import PackageRepository, AddressRepository
from models.package import (
    PackageIngestRequest,
    PackageIngestResponse,
    PackageStatus,
)
from models.address import ParsedAddress
from services.address_parser import get_address_parser
from services.geocoder import get_geocoder
from services.ocr_service import get_ocr_service
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ocr-text", response_model=PackageIngestResponse)
async def ingest_ocr_text(
    request: PackageIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest OCR text from edge device.
    
    This endpoint receives pre-processed OCR text from mobile/kiosk devices
    and processes it through the address parsing and geocoding pipeline.
    """
    logger.info(f"Ingesting package {request.package_id} from device {request.device_id}")
    
    # Create package record
    package_repo = PackageRepository(db)
    address_repo = AddressRepository(db)
    
    try:
        # Check if package already exists
        existing = await package_repo.get_by_package_id(request.package_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Package {request.package_id} already exists"
            )
        
        # Create package
        package = await package_repo.create(
            package_id=request.package_id,
            device_id=request.device_id,
            ocr_text=request.ocr_text,
            ocr_confidence=request.ocr_confidence,
            priority=request.priority,
            operator_id=request.operator_id,
            gps_lat=request.gps.lat if request.gps else None,
            gps_lon=request.gps.lon if request.gps else None,
        )
        
        package_uuid = uuid.UUID(package["id"])
        
        # Parse address
        parser = get_address_parser()
        parse_result = parser.parse(request.ocr_text)
        
        parsed_address_dict = parser.to_dict(parse_result)
        
        # Geocode if we have enough address info
        geocoded = False
        requires_verification = False
        lat, lon = None, None
        geocode_confidence = 0.0
        
        if parse_result.city or parse_result.subdistrict:
            geocoder = get_geocoder()
            geocode_query = parser.format_for_geocoding(parse_result)
            
            try:
                geocode_result = await geocoder.geocode(geocode_query)
                
                if geocode_result:
                    lat = geocode_result.lat
                    lon = geocode_result.lon
                    geocode_confidence = geocode_result.confidence
                    geocoded = True
                    
                    # Mark for verification if confidence is low
                    if geocode_confidence < 0.6:
                        requires_verification = True
                        
            except Exception as e:
                logger.warning(f"Geocoding failed for package {request.package_id}: {e}")
        
        # Determine if verification is needed
        if parse_result.confidence < 0.5 or request.ocr_confidence < settings.ocr_confidence_threshold:
            requires_verification = True
        
        # Create address record
        await address_repo.create(
            package_id=package_uuid,
            raw_text=request.ocr_text,
            street=parse_result.street,
            house_number=parse_result.house_number,
            rt=parse_result.rt,
            rw=parse_result.rw,
            neighborhood=parse_result.neighborhood,
            subdistrict=parse_result.subdistrict,
            city=parse_result.city,
            province=parse_result.province,
            postal_code=parse_result.postal_code,
            lat=lat,
            lon=lon,
            geocode_confidence=geocode_confidence,
            geocode_source="nominatim" if geocoded else None,
            requires_verification=requires_verification,
        )
        
        # Update package status
        if geocoded:
            status = PackageStatus.GEOCODED
        elif parse_result.confidence > 0.5:
            status = PackageStatus.PARSED
        else:
            status = PackageStatus.VERIFICATION_NEEDED
        
        await package_repo.update_status(package_uuid, status.value)
        
        await db.commit()
        
        return PackageIngestResponse(
            id=package["id"],
            package_id=request.package_id,
            status=status,
            message=f"Package ingested successfully. Parse confidence: {parse_result.confidence:.2f}",
            created_at=package["created_at"],
            parsed_address=parsed_address_dict,
            geocoded=geocoded,
            requires_verification=requires_verification,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest package {request.package_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image", response_model=PackageIngestResponse)
async def ingest_image(
    device_id: str = Form(...),
    package_id: str = Form(...),
    priority: str = Form("standard"),
    operator_id: Optional[str] = Form(None),
    gps_lat: Optional[float] = Form(None),
    gps_lon: Optional[float] = Form(None),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest image for server-side OCR.
    
    This endpoint receives package label images and performs OCR server-side.
    Use this for low-confidence edge OCR or devices without OCR capability.
    """
    logger.info(f"Ingesting image for package {package_id} from device {device_id}")
    
    # Validate image
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read image
    image_bytes = await image.read()
    
    if len(image_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Image size exceeds {settings.max_upload_size_mb}MB limit"
        )
    
    # Save image
    image_filename = f"{package_id}_{uuid.uuid4().hex[:8]}.jpg"
    image_path = os.path.join(settings.upload_dir, image_filename)
    
    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    
    # Perform OCR
    ocr_service = get_ocr_service()
    
    try:
        ocr_result = ocr_service.extract_text_from_bytes(image_bytes)
    except Exception as e:
        logger.error(f"OCR failed for package {package_id}: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")
    
    # Now process the OCR result through the same pipeline
    package_repo = PackageRepository(db)
    address_repo = AddressRepository(db)
    
    try:
        # Check if package already exists
        existing = await package_repo.get_by_package_id(package_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Package {package_id} already exists"
            )
        
        # Create package
        package = await package_repo.create(
            package_id=package_id,
            device_id=device_id,
            ocr_text=ocr_result.text,
            ocr_confidence=ocr_result.confidence,
            priority=priority,
            operator_id=operator_id,
            gps_lat=gps_lat,
            gps_lon=gps_lon,
            image_path=image_path,
        )
        
        package_uuid = uuid.UUID(package["id"])
        
        # Parse address
        parser = get_address_parser()
        parse_result = parser.parse(ocr_result.text)
        parsed_address_dict = parser.to_dict(parse_result)
        
        # Geocode
        geocoded = False
        requires_verification = ocr_result.confidence < settings.ocr_confidence_threshold
        lat, lon = None, None
        geocode_confidence = 0.0
        
        if parse_result.city or parse_result.subdistrict:
            geocoder = get_geocoder()
            geocode_query = parser.format_for_geocoding(parse_result)
            
            try:
                geocode_result = await geocoder.geocode(geocode_query)
                
                if geocode_result:
                    lat = geocode_result.lat
                    lon = geocode_result.lon
                    geocode_confidence = geocode_result.confidence
                    geocoded = True
                    
                    if geocode_confidence < 0.6:
                        requires_verification = True
                        
            except Exception as e:
                logger.warning(f"Geocoding failed for package {package_id}: {e}")
        
        if parse_result.confidence < 0.5:
            requires_verification = True
        
        # Create address record
        await address_repo.create(
            package_id=package_uuid,
            raw_text=ocr_result.text,
            street=parse_result.street,
            house_number=parse_result.house_number,
            rt=parse_result.rt,
            rw=parse_result.rw,
            neighborhood=parse_result.neighborhood,
            subdistrict=parse_result.subdistrict,
            city=parse_result.city,
            province=parse_result.province,
            postal_code=parse_result.postal_code,
            lat=lat,
            lon=lon,
            geocode_confidence=geocode_confidence,
            geocode_source="nominatim" if geocoded else None,
            requires_verification=requires_verification,
        )
        
        # Determine status
        if geocoded:
            status = PackageStatus.GEOCODED
        elif parse_result.confidence > 0.5:
            status = PackageStatus.PARSED
        else:
            status = PackageStatus.VERIFICATION_NEEDED
        
        await package_repo.update_status(package_uuid, status.value)
        
        await db.commit()
        
        return PackageIngestResponse(
            id=package["id"],
            package_id=package_id,
            status=status,
            message=f"Image processed. OCR confidence: {ocr_result.confidence:.2f}, Parse confidence: {parse_result.confidence:.2f}",
            created_at=package["created_at"],
            parsed_address=parsed_address_dict,
            geocoded=geocoded,
            requires_verification=requires_verification,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process image for package {package_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{package_id}")
async def get_package(
    package_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get package status and details."""
    package_repo = PackageRepository(db)
    address_repo = AddressRepository(db)
    
    package = await package_repo.get_by_package_id(package_id)
    
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Get address
    address = await address_repo.get_by_package_id(package["id"])
    
    return {
        "package": package,
        "address": address
    }
