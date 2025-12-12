"""
Indonesian Address Matcher Service.
Uses local administrative dataset for efficient address matching.
Implements HashMap + Lazy Fuzzy matching approach.
"""

import os
import csv
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from functools import lru_cache

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of address matching."""
    kelurahan: Optional[str] = None
    kelurahan_id: Optional[str] = None
    kecamatan: Optional[str] = None
    kecamatan_id: Optional[str] = None
    kabupaten: Optional[str] = None
    kabupaten_id: Optional[str] = None
    provinsi: Optional[str] = None
    provinsi_id: Optional[str] = None
    confidence: float = 0.0
    match_type: str = "none"  # "exact", "fuzzy", "none"


class AddressMatcher:
    """
    Efficient address matcher using local Indonesian administrative dataset.
    
    Uses HashMap for O(1) exact matching with lazy fuzzy matching fallback.
    Loads ~80K kelurahan, ~7K kecamatan, ~500 kabupaten, ~34 provinsi.
    """
    
    def __init__(self, dataset_dir: Optional[str] = None):
        """Initialize matcher with dataset directory."""
        if dataset_dir is None:
            # Default to dataset folder relative to this file
            dataset_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "dataset"
            )
        
        self.dataset_dir = dataset_dir
        self._loaded = False
        
        # HashMaps for O(1) lookup (normalized name -> data)
        self._provinsi_map: Dict[str, Dict] = {}
        self._kabupaten_map: Dict[str, Dict] = {}
        self._kecamatan_map: Dict[str, Dict] = {}
        self._kelurahan_map: Dict[str, Dict] = {}
        
        # ID lookup maps for hierarchical resolution
        self._provinsi_by_id: Dict[str, Dict] = {}
        self._kabupaten_by_id: Dict[str, Dict] = {}
        self._kecamatan_by_id: Dict[str, Dict] = {}
        
        # All names for fuzzy matching (sorted by length for efficiency)
        self._all_kecamatan_names: List[str] = []
        self._all_kelurahan_names: List[str] = []
        self._all_kabupaten_names: List[str] = []
        
    def _normalize(self, text: str) -> str:
        """Normalize text for matching (lowercase, strip)."""
        return text.lower().strip()
    
    def _load_datasets(self):
        """Load all CSV datasets into memory."""
        if self._loaded:
            return
            
        logger.info("Loading Indonesian administrative datasets...")
        
        # Load provinsi
        provinsi_path = os.path.join(self.dataset_dir, "provinsi.csv")
        if os.path.exists(provinsi_path):
            with open(provinsi_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name_normalized = self._normalize(row["provinsi_name"])
                    data = {
                        "id": row["provinsi_id"],
                        "name": row["provinsi_name"],
                        "name_normalized": name_normalized
                    }
                    self._provinsi_map[name_normalized] = data
                    self._provinsi_by_id[row["provinsi_id"]] = data
            logger.info(f"Loaded {len(self._provinsi_map)} provinsi")
        
        # Load kabupaten
        kabupaten_path = os.path.join(self.dataset_dir, "kabupaten.csv")
        if os.path.exists(kabupaten_path):
            with open(kabupaten_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name_normalized = self._normalize(row["kabupaten_name"])
                    # Also create normalized version without KOTA/KABUPATEN prefix
                    name_clean = name_normalized.replace("kota ", "").replace("kabupaten ", "")
                    
                    data = {
                        "id": row["kabupaten_id"],
                        "name": row["kabupaten_name"],
                        "name_normalized": name_normalized,
                        "name_clean": name_clean,
                        "provinsi_id": row["provinsi_id"]
                    }
                    self._kabupaten_map[name_normalized] = data
                    self._kabupaten_map[name_clean] = data  # Also index by clean name
                    self._kabupaten_by_id[row["kabupaten_id"]] = data
                    self._all_kabupaten_names.append(name_clean)
            logger.info(f"Loaded {len(self._kabupaten_by_id)} kabupaten")
        
        # Load kecamatan
        kecamatan_path = os.path.join(self.dataset_dir, "kecamatan.csv")
        if os.path.exists(kecamatan_path):
            with open(kecamatan_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name_normalized = self._normalize(row["kecamatan_name"])
                    data = {
                        "id": row["kecamatan_id"],
                        "name": row["kecamatan_name"],
                        "name_normalized": name_normalized,
                        "kabupaten_id": row["kabupaten_id"]
                    }
                    self._kecamatan_map[name_normalized] = data
                    self._kecamatan_by_id[row["kecamatan_id"]] = data
                    self._all_kecamatan_names.append(name_normalized)
            logger.info(f"Loaded {len(self._kecamatan_map)} kecamatan")
        
        # Load kelurahan
        kelurahan_path = os.path.join(self.dataset_dir, "kelurahan.csv")
        if os.path.exists(kelurahan_path):
            with open(kelurahan_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name_normalized = self._normalize(row["kelurahan_name"])
                    data = {
                        "id": row["kelurahan_id"],
                        "name": row["kelurahan_name"],
                        "name_normalized": name_normalized,
                        "kecamatan_id": row["kecamatan_id"]
                    }
                    # Note: Multiple kelurahan can have same name
                    if name_normalized not in self._kelurahan_map:
                        self._kelurahan_map[name_normalized] = []
                    self._kelurahan_map[name_normalized].append(data)
                    self._all_kelurahan_names.append(name_normalized)
            logger.info(f"Loaded {len(self._kelurahan_map)} unique kelurahan names")
        
        self._loaded = True
        logger.info("Address datasets loaded successfully")
    
    def _fuzzy_match(self, query: str, candidates: List[str], threshold: float = 85) -> Optional[Tuple[str, float]]:
        """
        Find best fuzzy match from candidates using rapidfuzz.
        
        Args:
            query: Search query
            candidates: List of candidate strings to match against
            threshold: Minimum similarity score (0-100, default 85)
            
        Returns:
            (matched_name, similarity_score as 0-1) or None if no match above threshold.
        """
        query_normalized = self._normalize(query)
        
        # Use rapidfuzz process.extractOne for fast matching
        result = process.extractOne(
            query_normalized,
            candidates,
            scorer=fuzz.ratio,
            score_cutoff=threshold
        )
        
        if result:
            matched_name, score, _ = result
            return (matched_name, score / 100.0)  # Convert to 0-1 scale
        return None
    
    def _resolve_hierarchy(self, result: MatchResult) -> MatchResult:
        """Resolve full hierarchy from matched data."""
        # If we have kecamatan, resolve kabupaten and provinsi
        if result.kecamatan_id and result.kecamatan_id in self._kecamatan_by_id:
            kec_data = self._kecamatan_by_id[result.kecamatan_id]
            kab_id = kec_data.get("kabupaten_id")
            
            if kab_id and kab_id in self._kabupaten_by_id:
                kab_data = self._kabupaten_by_id[kab_id]
                result.kabupaten = kab_data["name"]
                result.kabupaten_id = kab_id
                
                prov_id = kab_data.get("provinsi_id")
                if prov_id and prov_id in self._provinsi_by_id:
                    prov_data = self._provinsi_by_id[prov_id]
                    result.provinsi = prov_data["name"]
                    result.provinsi_id = prov_id
        
        # If we have kabupaten but no provinsi
        elif result.kabupaten_id and result.kabupaten_id in self._kabupaten_by_id:
            kab_data = self._kabupaten_by_id[result.kabupaten_id]
            prov_id = kab_data.get("provinsi_id")
            if prov_id and prov_id in self._provinsi_by_id:
                prov_data = self._provinsi_by_id[prov_id]
                result.provinsi = prov_data["name"]
                result.provinsi_id = prov_id
        
        return result
    
    def match_address(self, text_segments: List[str]) -> MatchResult:
        """
        Match address segments against administrative dataset.
        
        Args:
            text_segments: List of address parts (e.g., ["49", "Lowokwaru", "Malang"])
            
        Returns:
            MatchResult with matched locations and confidence
        """
        self._load_datasets()
        
        result = MatchResult()
        matches_found = 0
        total_confidence = 0.0
        
        for segment in text_segments:
            segment_normalized = self._normalize(segment)
            
            # Skip numeric-only segments (house numbers, RT/RW)
            if segment_normalized.isdigit():
                continue
            
            # Skip very short segments
            if len(segment_normalized) < 3:
                continue
            
            # Try exact match on kecamatan first (most common case)
            if segment_normalized in self._kecamatan_map:
                kec_data = self._kecamatan_map[segment_normalized]
                result.kecamatan = kec_data["name"]
                result.kecamatan_id = kec_data["id"]
                result.match_type = "exact"
                matches_found += 1
                total_confidence += 1.0
                logger.debug(f"Exact match kecamatan: {segment} -> {kec_data['name']}")
                continue
            
            # Try exact match on kabupaten
            if segment_normalized in self._kabupaten_map:
                kab_data = self._kabupaten_map[segment_normalized]
                result.kabupaten = kab_data["name"]
                result.kabupaten_id = kab_data["id"]
                result.match_type = "exact"
                matches_found += 1
                total_confidence += 1.0
                logger.debug(f"Exact match kabupaten: {segment} -> {kab_data['name']}")
                continue
            
            # Try exact match on kelurahan
            if segment_normalized in self._kelurahan_map:
                kel_list = self._kelurahan_map[segment_normalized]
                # Take first one (could be improved with context)
                kel_data = kel_list[0]
                result.kelurahan = kel_data["name"]
                result.kelurahan_id = kel_data["id"]
                # Also get kecamatan from kelurahan
                kec_id = kel_data.get("kecamatan_id")
                if kec_id and kec_id in self._kecamatan_by_id:
                    kec_data = self._kecamatan_by_id[kec_id]
                    result.kecamatan = kec_data["name"]
                    result.kecamatan_id = kec_id
                result.match_type = "exact"
                matches_found += 1
                total_confidence += 1.0
                logger.debug(f"Exact match kelurahan: {segment} -> {kel_data['name']}")
                continue
            
            # Try exact match on provinsi
            if segment_normalized in self._provinsi_map:
                prov_data = self._provinsi_map[segment_normalized]
                result.provinsi = prov_data["name"]
                result.provinsi_id = prov_data["id"]
                result.match_type = "exact"
                matches_found += 1
                total_confidence += 1.0
                continue
            
            # Fuzzy matching fallback (only for longer segments)
            if len(segment_normalized) >= 4:
                # Try fuzzy match on kecamatan
                fuzzy_result = self._fuzzy_match(
                    segment_normalized, 
                    self._all_kecamatan_names, 
                    threshold=80
                )
                if fuzzy_result:
                    matched_name, score = fuzzy_result
                    kec_data = self._kecamatan_map[matched_name]
                    result.kecamatan = kec_data["name"]
                    result.kecamatan_id = kec_data["id"]
                    result.match_type = "fuzzy"
                    matches_found += 1
                    total_confidence += score
                    logger.debug(f"Fuzzy match kecamatan: {segment} -> {kec_data['name']} ({score:.2f})")
                    continue
                
                # Try fuzzy match on kabupaten
                fuzzy_result = self._fuzzy_match(
                    segment_normalized,
                    self._all_kabupaten_names,
                    threshold=80
                )
                if fuzzy_result:
                    matched_name, score = fuzzy_result
                    kab_data = self._kabupaten_map[matched_name]
                    result.kabupaten = kab_data["name"]
                    result.kabupaten_id = kab_data["id"]
                    result.match_type = "fuzzy"
                    matches_found += 1
                    total_confidence += score
                    logger.debug(f"Fuzzy match kabupaten: {segment} -> {kab_data['name']} ({score:.2f})")
                    continue
        
        # Resolve full hierarchy
        result = self._resolve_hierarchy(result)
        
        # Calculate final confidence
        if matches_found > 0:
            result.confidence = total_confidence / matches_found
        
        return result
    
    def match_text(self, raw_text: str) -> MatchResult:
        """
        Match raw address text against dataset.
        
        Splits text by comma and other delimiters, then matches each segment.
        """
        # Split by common delimiters
        import re
        segments = re.split(r'[,\n;]+', raw_text)
        segments = [s.strip() for s in segments if s.strip()]
        
        return self.match_address(segments)


# Singleton instance
_matcher_instance: Optional[AddressMatcher] = None


def get_address_matcher() -> AddressMatcher:
    """Get singleton address matcher instance."""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = AddressMatcher()
    return _matcher_instance
