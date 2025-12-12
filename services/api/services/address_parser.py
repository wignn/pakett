"""
Indonesian Address Parser Service.
Uses regex-based parsing with OCR error correction.
Designed for Indonesian address format with RT/RW support.
"""

import re
from typing import Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of address parsing."""
    street: Optional[str] = None
    house_number: Optional[str] = None
    rt: Optional[str] = None
    rw: Optional[str] = None
    neighborhood: Optional[str] = None  # Kelurahan
    subdistrict: Optional[str] = None   # Kecamatan
    city: Optional[str] = None          # Kota/Kabupaten
    province: Optional[str] = None
    postal_code: Optional[str] = None
    confidence: float = 0.0
    corrections: List[str] = None
    
    def __post_init__(self):
        if self.corrections is None:
            self.corrections = []


class AddressParser:
    """
    Parser for Indonesian addresses extracted from OCR.
    
    Handles common formats like:
    - Jalan Merdeka No. 45 RT 02/RW 03, Kebayoran Lama, Jakarta Selatan 12220
    - Jl. Sudirman 123, Kel. Menteng, Kec. Menteng, Jakarta Pusat
    - Komplek ABC Blok D No 5, Tangerang 15111
    """
    
    # Common OCR corrections for Indonesian addresses
    OCR_CORRECTIONS = [
        # Street prefixes
        (r'\bJ[l1]n?\b', 'Jalan'),
        (r'\bJ[l1]\.\s*', 'Jalan '),
        (r'\bGg\b', 'Gang'),
        (r'\bKomp\b', 'Komplek'),
        (r'\bKomp\.\s*', 'Komplek '),
        (r'\bPerum\b', 'Perumahan'),
        
        # Number indicators
        (r'\bNo\.\s*', 'No. '),
        (r'\bNomor\s*', 'No. '),
        (r'\bN[o0]\b', 'No'),
        
        # RT/RW variations
        (r'\bRt\.?\s*', 'RT '),
        (r'\bRw\.?\s*', 'RW '),
        (r'RT\s*/\s*RW', 'RT/RW'),
        
        # Administrative divisions
        (r'\bKe[l1]\.\s*', 'Kel. '),
        (r'\bKec\.\s*', 'Kec. '),
        (r'\bKab\.\s*', 'Kab. '),
        
        # City abbreviations
        (r'\bJakse[l1]\b', 'Jakarta Selatan'),
        (r'\bJakut\b', 'Jakarta Utara'),
        (r'\bJakbar\b', 'Jakarta Barat'),
        (r'\bJaktim\b', 'Jakarta Timur'),
        (r'\bJakpus\b', 'Jakarta Pusat'),
        (r'\bJkt\b', 'Jakarta'),
        (r'\bBdg\b', 'Bandung'),
        (r'\bSby\b', 'Surabaya'),
        (r'\bMdn\b', 'Medan'),
        (r'\bSmg\b', 'Semarang'),
        (r'\bYk\b', 'Yogyakarta'),
        (r'\bJogja\b', 'Yogyakarta'),
        
        # Common OCR errors (0/O, 1/l/I, etc.)
        (r'(?<=[A-Za-z])0(?=[A-Za-z])', 'O'),  # 0 -> O between letters
        (r'(?<=[0-9])O(?=[0-9])', '0'),  # O -> 0 between numbers
        (r'(?<=[0-9])l(?=[0-9])', '1'),  # l -> 1 between numbers
        (r'(?<=[0-9])I(?=[0-9])', '1'),  # I -> 1 between numbers
    ]
    
    # Patterns for extraction
    PATTERNS = {
        # Postal code (5 digits)
        'postal_code': r'\b(\d{5})\b',
        
        # RT/RW patterns
        'rt_rw': r'(?:RT\.?\s*)(\d{1,3})(?:\s*/\s*|\s+)(?:RW\.?\s*)(\d{1,3})',
        'rt_only': r'(?:RT\.?\s*)(\d{1,3})(?!\s*/?\s*RW)',
        'rw_only': r'(?:RW\.?\s*)(\d{1,3})',
        
        # House number patterns
        'house_number': [
            r'(?:No\.?\s*)(\d+[A-Za-z]?)',
            r'(?:Nomor\s*)(\d+[A-Za-z]?)',
            r'(?:Blok\s*[A-Za-z]+\s*(?:No\.?\s*)?)(\d+[A-Za-z]?)',
        ],
        
        # Street patterns
        'street': [
            r'((?:Jalan|Jl\.?)\s+[A-Za-z][A-Za-z\s\.]+?)(?=\s+(?:No|RT|Blok|\d))',
            r'((?:Gang|Gg\.?)\s+[A-Za-z][A-Za-z\s\.]+?)(?=\s+(?:No|RT|\d))',
            r'((?:Komplek|Komp\.?|Perumahan|Perum\.?)\s+[A-Za-z][A-Za-z\s\.]+?)(?=\s+(?:Blok|No|RT|\d))',
        ],
        
        # City patterns (major Indonesian cities)
        'cities': [
            'Jakarta Selatan', 'Jakarta Utara', 'Jakarta Barat', 
            'Jakarta Timur', 'Jakarta Pusat', 'Jakarta',
            'Bandung', 'Surabaya', 'Medan', 'Semarang', 'Makassar',
            'Palembang', 'Tangerang', 'Depok', 'Bekasi', 'Bogor',
            'Yogyakarta', 'Malang', 'Solo', 'Denpasar', 'Batam',
        ],
        
        # Subdistrict (Kecamatan) pattern
        'subdistrict': r'(?:Kec(?:amatan)?\.?\s*)([A-Za-z][A-Za-z\s]+?)(?=,|\d|Kota|Kab|$)',
        
        # Neighborhood (Kelurahan) pattern
        'neighborhood': r'(?:Kel(?:urahan)?\.?\s*)([A-Za-z][A-Za-z\s]+?)(?=,|Kec|$)',
    }
    
    def __init__(self):
        """Initialize the address parser."""
        # Compile regex patterns for efficiency
        self._compiled_corrections = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.OCR_CORRECTIONS
        ]
        
        # Compile city pattern
        cities_pattern = '|'.join(re.escape(city) for city in self.PATTERNS['cities'])
        self._city_pattern = re.compile(cities_pattern, re.IGNORECASE)
    
    def apply_corrections(self, text: str) -> Tuple[str, List[str]]:
        """
        Apply OCR error corrections to the text.
        
        Returns:
            Tuple of (corrected_text, list_of_corrections_applied)
        """
        corrections = []
        corrected = text
        
        for pattern, replacement in self._compiled_corrections:
            new_text = pattern.sub(replacement, corrected)
            if new_text != corrected:
                corrections.append(f"{pattern.pattern} -> {replacement}")
                corrected = new_text
        
        return corrected, corrections
    
    def parse(self, raw_text: str, apply_corrections: bool = True) -> ParseResult:
        """
        Parse an Indonesian address string into components.
        
        Args:
            raw_text: Raw address text (possibly from OCR)
            apply_corrections: Whether to apply OCR error corrections
            
        Returns:
            ParseResult with extracted address components
        """
        result = ParseResult()
        
        if not raw_text:
            return result
        
        text = raw_text.strip()
        corrections = []
        
        # Apply OCR corrections if enabled
        if apply_corrections:
            text, corrections = self.apply_corrections(text)
            result.corrections = corrections
        
        # Track confidence based on what we extract
        confidence_score = 0.0
        max_possible = 7.0  # street, number, rt, rw, subdistrict, city, postal
        
        # Extract postal code (high confidence marker)
        postal_match = re.search(self.PATTERNS['postal_code'], text)
        if postal_match:
            result.postal_code = postal_match.group(1)
            confidence_score += 1.0
        
        # Extract RT/RW
        rt_rw_match = re.search(self.PATTERNS['rt_rw'], text, re.IGNORECASE)
        if rt_rw_match:
            result.rt = rt_rw_match.group(1).zfill(2)
            result.rw = rt_rw_match.group(2).zfill(2)
            confidence_score += 1.0
        else:
            # Try individual RT/RW
            rt_match = re.search(self.PATTERNS['rt_only'], text, re.IGNORECASE)
            if rt_match:
                result.rt = rt_match.group(1).zfill(2)
                confidence_score += 0.5
            
            rw_match = re.search(self.PATTERNS['rw_only'], text, re.IGNORECASE)
            if rw_match:
                result.rw = rw_match.group(1).zfill(2)
                confidence_score += 0.5
        
        # Extract house number
        for pattern in self.PATTERNS['house_number']:
            number_match = re.search(pattern, text, re.IGNORECASE)
            if number_match:
                result.house_number = number_match.group(1)
                confidence_score += 1.0
                break
        
        # Extract street name
        for pattern in self.PATTERNS['street']:
            street_match = re.search(pattern, text, re.IGNORECASE)
            if street_match:
                result.street = street_match.group(1).strip()
                confidence_score += 1.0
                break
        
        # Extract city
        city_match = self._city_pattern.search(text)
        if city_match:
            result.city = city_match.group(0).title()
            confidence_score += 1.0
        
        # Extract subdistrict (Kecamatan)
        subdistrict_match = re.search(self.PATTERNS['subdistrict'], text, re.IGNORECASE)
        if subdistrict_match:
            result.subdistrict = subdistrict_match.group(1).strip().title()
            confidence_score += 1.0
        else:
            # Try to extract from comma-separated parts
            result.subdistrict = self._extract_subdistrict_from_parts(text, result)
            if result.subdistrict:
                confidence_score += 0.7
        
        # Extract neighborhood (Kelurahan)
        neighborhood_match = re.search(self.PATTERNS['neighborhood'], text, re.IGNORECASE)
        if neighborhood_match:
            result.neighborhood = neighborhood_match.group(1).strip().title()
            confidence_score += 0.5
        
        # Calculate confidence
        result.confidence = min(confidence_score / max_possible, 1.0)
        
        logger.debug(f"Parsed address: {result}")
        return result
    
    def _extract_subdistrict_from_parts(self, text: str, result: ParseResult) -> Optional[str]:
        """
        Try to extract subdistrict from comma-separated parts.
        Assumes format: Street, Subdistrict, City, PostalCode
        """
        # Split by comma and clean
        parts = [p.strip() for p in text.split(',') if p.strip()]
        
        # If we have city and postal code, subdistrict might be the part before city
        if len(parts) >= 2 and result.city:
            for i, part in enumerate(parts):
                if result.city.lower() in part.lower():
                    # Check if previous part could be subdistrict
                    if i > 0:
                        candidate = parts[i-1]
                        # Filter out street names and numbers
                        if not re.search(r'\b(?:Jalan|Jl|Gang|Gg|No|RT|RW|\d{5})\b', candidate, re.IGNORECASE):
                            return candidate.title()
        
        return None
    
    def to_dict(self, result: ParseResult) -> dict:
        """Convert ParseResult to dictionary."""
        return {
            "street": result.street,
            "house_number": result.house_number,
            "rt": result.rt,
            "rw": result.rw,
            "neighborhood": result.neighborhood,
            "subdistrict": result.subdistrict,
            "city": result.city,
            "province": result.province,
            "postal_code": result.postal_code,
            "confidence": result.confidence,
            "corrections_applied": result.corrections,
        }
    
    def format_for_geocoding(self, result: ParseResult) -> str:
        """
        Format parsed address for geocoding query.
        Creates a normalized string suitable for geocoding APIs.
        """
        parts = []
        
        if result.street:
            if result.house_number:
                parts.append(f"{result.street} {result.house_number}")
            else:
                parts.append(result.street)
        
        if result.neighborhood:
            parts.append(result.neighborhood)
        
        if result.subdistrict:
            parts.append(result.subdistrict)
        
        if result.city:
            parts.append(result.city)
        
        if result.postal_code:
            parts.append(result.postal_code)
        
        parts.append("Indonesia")
        
        return ", ".join(parts)


# Singleton instance
_parser_instance = None


def get_address_parser() -> AddressParser:
    """Get singleton address parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = AddressParser()
    return _parser_instance
