"""
Address API endpoints.
Handles address parsing, normalization, and geocoding.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.address import (
    AddressParseRequest,
    AddressParseResponse,
    AddressGeocodeRequest,
    AddressGeocodeResponse,
    ParsedAddress,
    GeoLocation,
)
from services.address_parser import get_address_parser
from services.geocoder import get_geocoder

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/parse", response_model=AddressParseResponse)
async def parse_address(request: AddressParseRequest):
    """
    Parse raw address text into components.
    
    Extracts Indonesian address components:
    - Street name (Jalan/Gang)
    - House number
    - RT/RW
    - Kelurahan (neighborhood)
    - Kecamatan (subdistrict)
    - City/Kabupaten
    - Postal code
    
    Also applies OCR error corrections if enabled.
    """
    logger.info(f"Parsing address: {request.raw_text[:50]}...")
    
    parser = get_address_parser()
    
    try:
        result = parser.parse(
            request.raw_text,
            apply_corrections=request.apply_corrections
        )
        
        parsed = ParsedAddress(
            raw_text=request.raw_text,
            street=result.street,
            house_number=result.house_number,
            rt=result.rt,
            rw=result.rw,
            neighborhood=result.neighborhood,
            subdistrict=result.subdistrict,
            city=result.city,
            province=result.province,
            postal_code=result.postal_code,
            confidence=result.confidence,
            corrections_applied=result.corrections,
        )
        
        return AddressParseResponse(
            success=True,
            address=parsed,
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Address parsing failed: {e}")
        return AddressParseResponse(
            success=False,
            address=None,
            errors=[str(e)]
        )


@router.post("/geocode", response_model=AddressGeocodeResponse)
async def geocode_address(request: AddressGeocodeRequest):
    """
    Geocode a parsed address to coordinates.
    
    Uses configured geocoding provider (Nominatim by default).
    Results are cached in Redis for 7 days.
    """
    parser = get_address_parser()
    geocoder = get_geocoder()
    
    # Convert ParsedAddress to ParseResult for formatting
    from services.address_parser import ParseResult
    
    parse_result = ParseResult(
        street=request.address.street,
        house_number=request.address.house_number,
        rt=request.address.rt,
        rw=request.address.rw,
        neighborhood=request.address.neighborhood,
        subdistrict=request.address.subdistrict,
        city=request.address.city,
        province=request.address.province,
        postal_code=request.address.postal_code,
    )
    
    # Format address for geocoding
    geocode_query = parser.format_for_geocoding(parse_result)
    
    logger.info(f"Geocoding: {geocode_query[:50]}...")
    
    try:
        result = await geocoder.geocode(
            geocode_query,
            use_cache=request.use_cache
        )
        
        if result:
            location = GeoLocation(
                lat=result.lat,
                lon=result.lon,
                confidence=result.confidence,
                source=result.source,
                place_id=result.place_id,
                display_name=result.display_name,
                cached=result.cached,
            )
            
            requires_verification = result.confidence < 0.6
            
            return AddressGeocodeResponse(
                success=True,
                location=location,
                address=request.address,
                requires_verification=requires_verification,
                alternatives=[],
            )
        else:
            return AddressGeocodeResponse(
                success=False,
                location=None,
                address=request.address,
                requires_verification=True,
                error="No geocoding result found",
            )
            
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        return AddressGeocodeResponse(
            success=False,
            location=None,
            address=request.address,
            requires_verification=True,
            error=str(e),
        )


@router.post("/batch-geocode")
async def batch_geocode(
    addresses: List[AddressParseRequest],
    use_cache: bool = True
):
    """
    Geocode multiple addresses in batch.
    
    More efficient than individual calls due to concurrency control.
    """
    parser = get_address_parser()
    geocoder = get_geocoder()
    
    results = []
    
    # Parse all addresses first
    geocode_queries = []
    parsed_addresses = []
    
    for addr_request in addresses:
        parse_result = parser.parse(addr_request.raw_text, apply_corrections=True)
        geocode_query = parser.format_for_geocoding(parse_result)
        geocode_queries.append(geocode_query)
        parsed_addresses.append(parse_result)
    
    # Batch geocode
    geocode_results = await geocoder.geocode_batch(
        geocode_queries,
        use_cache=use_cache,
        max_concurrent=3  # Be nice to external API
    )
    
    # Combine results
    for i, addr_request in enumerate(addresses):
        parse_result = parsed_addresses[i]
        geocode_result = geocode_results.get(geocode_queries[i])
        
        result = {
            "raw_text": addr_request.raw_text,
            "parsed": parser.to_dict(parse_result),
            "geocoded": False,
            "lat": None,
            "lon": None,
            "confidence": None,
        }
        
        if geocode_result:
            result["geocoded"] = True
            result["lat"] = geocode_result.lat
            result["lon"] = geocode_result.lon
            result["confidence"] = geocode_result.confidence
            result["cached"] = geocode_result.cached
        
        results.append(result)
    
    return {
        "total": len(results),
        "geocoded": sum(1 for r in results if r["geocoded"]),
        "results": results
    }


@router.get("/corrections")
async def get_ocr_corrections():
    """
    Get the list of OCR correction rules.
    
    Useful for understanding what corrections are applied
    and for debugging parsing issues.
    """
    parser = get_address_parser()
    
    return {
        "corrections": [
            {"pattern": p.pattern, "replacement": r}
            for p, r in parser._compiled_corrections
        ]
    }
