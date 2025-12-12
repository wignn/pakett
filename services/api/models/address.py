"""
Pydantic models for address parsing and geocoding.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ParsedAddress(BaseModel):
    """Parsed and normalized Indonesian address."""
    
    raw_text: str = Field(..., description="Original raw address text")
    street: Optional[str] = Field(default=None, description="Street name (Jalan)")
    house_number: Optional[str] = Field(default=None, description="House/building number")
    rt: Optional[str] = Field(default=None, description="RT (Rukun Tetangga)")
    rw: Optional[str] = Field(default=None, description="RW (Rukun Warga)")
    neighborhood: Optional[str] = Field(default=None, description="Kelurahan/Desa")
    subdistrict: Optional[str] = Field(default=None, description="Kecamatan")
    city: Optional[str] = Field(default=None, description="Kota/Kabupaten")
    province: Optional[str] = Field(default=None, description="Provinsi")
    postal_code: Optional[str] = Field(default=None, description="Kode Pos")
    country: str = Field(default="Indonesia")
    
    # Parsing metadata
    confidence: float = Field(default=0.0, ge=0, le=1, description="Parsing confidence")
    corrections_applied: List[str] = Field(default_factory=list, description="OCR corrections applied")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "raw_text": "Jalan Merdeka 45 Rt 02 Rw 03, Kebayoran Lama, Jakarta Selatan 12220",
                    "street": "Jalan Merdeka",
                    "house_number": "45",
                    "rt": "02",
                    "rw": "03",
                    "subdistrict": "Kebayoran Lama",
                    "city": "Jakarta Selatan",
                    "postal_code": "12220",
                    "confidence": 0.92,
                    "corrections_applied": ["Jln -> Jalan"]
                }
            ]
        }
    }


class AddressParseRequest(BaseModel):
    """Request to parse raw address text."""
    
    raw_text: str = Field(..., min_length=5, description="Raw address text to parse")
    apply_corrections: bool = Field(default=True, description="Apply OCR error corrections")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "raw_text": "Jln Merdeka No.45 RT02/RW03 Kebayoran Lama Jaksel 12220",
                    "apply_corrections": True
                }
            ]
        }
    }


class AddressParseResponse(BaseModel):
    """Response with parsed address components."""
    
    success: bool = Field(..., description="Whether parsing was successful")
    address: Optional[ParsedAddress] = Field(default=None, description="Parsed address")
    errors: List[str] = Field(default_factory=list, description="Parsing errors if any")


class GeoLocation(BaseModel):
    """Geocoded location with metadata."""
    
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    confidence: float = Field(default=0.0, ge=0, le=1, description="Geocoding confidence")
    source: str = Field(default="nominatim", description="Geocoding provider used")
    place_id: Optional[str] = Field(default=None, description="Place ID from provider")
    display_name: Optional[str] = Field(default=None, description="Full display name")
    cached: bool = Field(default=False, description="Result was from cache")


class AddressGeocodeRequest(BaseModel):
    """Request to geocode an address."""
    
    address: ParsedAddress = Field(..., description="Parsed address to geocode")
    use_cache: bool = Field(default=True, description="Check cache first")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "address": {
                        "raw_text": "Jalan Merdeka 45, Kebayoran Lama, Jakarta Selatan",
                        "street": "Jalan Merdeka",
                        "house_number": "45",
                        "subdistrict": "Kebayoran Lama",
                        "city": "Jakarta Selatan"
                    },
                    "use_cache": True
                }
            ]
        }
    }


class AddressGeocodeResponse(BaseModel):
    """Response with geocoded location."""
    
    success: bool = Field(..., description="Whether geocoding was successful")
    location: Optional[GeoLocation] = Field(default=None, description="Geocoded location")
    address: ParsedAddress = Field(..., description="Input address")
    requires_verification: bool = Field(default=False, description="Low confidence, needs verification")
    alternatives: List[GeoLocation] = Field(default_factory=list, description="Alternative matches")
    error: Optional[str] = Field(default=None, description="Error message if failed")
