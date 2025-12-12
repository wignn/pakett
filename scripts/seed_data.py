#!/usr/bin/env python3
"""
Synthetic data generator for testing.
Generates sample packages with Indonesian addresses for Jakarta area.
"""

import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

# Sample Indonesian address components
STREETS = [
    "Jalan Sudirman", "Jalan Thamrin", "Jalan Gatot Subroto", "Jalan Rasuna Said",
    "Jalan Kuningan", "Jalan Casablanca", "Jalan Merdeka", "Jalan Menteng",
    "Jalan Kemang", "Jalan Tebet", "Jalan Fatmawati", "Jalan Cilandak",
    "Jalan Tendean", "Jalan Panglima Polim", "Jalan Senopati", "Jalan Gunawarman",
    "Jalan Kebayoran", "Jalan Wijaya", "Jalan Blok M", "Jalan Radio Dalam",
    "Gang Mawar", "Gang Kenanga", "Gang Melati", "Komplek Taman Indah",
    "Perumahan Graha Sejahtera", "Jalan Raya Pasar Minggu", "Jalan TB Simatupang",
]

SUBDISTRICTS = [
    ("Menteng", "Jakarta Pusat"),
    ("Tanah Abang", "Jakarta Pusat"),
    ("Gambir", "Jakarta Pusat"),
    ("Kebayoran Baru", "Jakarta Selatan"),
    ("Kebayoran Lama", "Jakarta Selatan"),
    ("Setiabudi", "Jakarta Selatan"),
    ("Tebet", "Jakarta Selatan"),
    ("Pancoran", "Jakarta Selatan"),
    ("Pasar Minggu", "Jakarta Selatan"),
    ("Cilandak", "Jakarta Selatan"),
    ("Mampang Prapatan", "Jakarta Selatan"),
    ("Kemang", "Jakarta Selatan"),
    ("Kelapa Gading", "Jakarta Utara"),
    ("Tanjung Priok", "Jakarta Utara"),
    ("Pademangan", "Jakarta Utara"),
    ("Cengkareng", "Jakarta Barat"),
    ("Grogol Petamburan", "Jakarta Barat"),
    ("Kebon Jeruk", "Jakarta Barat"),
    ("Cakung", "Jakarta Timur"),
    ("Jatinegara", "Jakarta Timur"),
    ("Duren Sawit", "Jakarta Timur"),
    ("Matraman", "Jakarta Timur"),
]

POSTAL_CODES = {
    "Jakarta Pusat": ["10110", "10120", "10130", "10210", "10220", "10310", "10320"],
    "Jakarta Selatan": ["12110", "12120", "12130", "12140", "12150", "12210", "12220", "12310", "12410", "12510"],
    "Jakarta Utara": ["14110", "14120", "14130", "14210", "14220", "14310", "14320"],
    "Jakarta Barat": ["11110", "11120", "11130", "11210", "11220", "11310", "11410", "11420"],
    "Jakarta Timur": ["13110", "13120", "13130", "13210", "13220", "13310", "13410", "13510"],
}

# Jakarta area bounding box
JAKARTA_BOUNDS = {
    "min_lat": -6.38,
    "max_lat": -6.08,
    "min_lon": 106.65,
    "max_lon": 107.00,
}


def generate_address() -> Dict:
    """Generate a random Indonesian address."""
    street = random.choice(STREETS)
    house_number = str(random.randint(1, 200))
    rt = str(random.randint(1, 20)).zfill(2)
    rw = str(random.randint(1, 15)).zfill(2)
    subdistrict, city = random.choice(SUBDISTRICTS)
    postal_code = random.choice(POSTAL_CODES.get(city, ["12345"]))
    
    # Generate coordinates (approximate)
    lat = random.uniform(JAKARTA_BOUNDS["min_lat"], JAKARTA_BOUNDS["max_lat"])
    lon = random.uniform(JAKARTA_BOUNDS["min_lon"], JAKARTA_BOUNDS["max_lon"])
    
    # Build raw address text (simulating OCR output)
    variations = [
        f"{street} No. {house_number} RT {rt}/RW {rw}, {subdistrict}, {city} {postal_code}",
        f"{street} {house_number}, RT{rt} RW{rw}, Kel. {subdistrict}, {city} {postal_code}",
        f"{street} No {house_number} RT {rt} RW {rw} {subdistrict} {city}",
        f"Jl. {street.replace('Jalan ', '')} {house_number}, {subdistrict}, {city} {postal_code}",
    ]
    
    raw_text = random.choice(variations)
    
    # Simulate OCR errors occasionally
    if random.random() < 0.15:
        raw_text = simulate_ocr_errors(raw_text)
    
    return {
        "raw_text": raw_text,
        "street": street,
        "house_number": house_number,
        "rt": rt,
        "rw": rw,
        "subdistrict": subdistrict,
        "city": city,
        "postal_code": postal_code,
        "lat": lat,
        "lon": lon,
    }


def simulate_ocr_errors(text: str) -> str:
    """Simulate common OCR errors."""
    replacements = [
        ("Jalan", "Jln"),
        ("Jalan", "J1n"),
        ("No.", "N0."),
        ("0", "O"),  # In numbers only
        ("1", "l"),  # In numbers only
        (",", "."),
    ]
    
    result = text
    for old, new in random.sample(replacements, k=min(2, len(replacements))):
        if random.random() < 0.3:
            result = result.replace(old, new, 1)
    
    return result


def generate_package(index: int) -> Dict:
    """Generate a sample package with address."""
    address = generate_address()
    
    package_id = f"PKT{datetime.now().strftime('%Y%m%d')}{str(index).zfill(6)}"
    device_id = f"scanner-{random.randint(1, 50):02d}"
    
    # OCR confidence (slightly lower if errors were simulated)
    if "J1n" in address["raw_text"] or "N0" in address["raw_text"]:
        ocr_confidence = random.uniform(0.5, 0.75)
    else:
        ocr_confidence = random.uniform(0.75, 0.98)
    
    return {
        "device_id": device_id,
        "package_id": package_id,
        "ocr_text": address["raw_text"],
        "ocr_confidence": round(ocr_confidence, 2),
        "timestamp": datetime.now().isoformat(),
        "gps": {
            "lat": round(address["lat"], 6),
            "lon": round(address["lon"], 6),
        },
        "priority": random.choice(["standard", "standard", "standard", "high", "urgent"]),
        "_ground_truth": {
            "street": address["street"],
            "house_number": address["house_number"],
            "rt": address["rt"],
            "rw": address["rw"],
            "subdistrict": address["subdistrict"],
            "city": address["city"],
            "postal_code": address["postal_code"],
            "lat": address["lat"],
            "lon": address["lon"],
        }
    }


def generate_vehicles(count: int = 5) -> List[Dict]:
    """Generate sample vehicles."""
    vehicle_types = ["motorcycle", "motorcycle", "motorcycle", "van", "truck"]
    capacities = {"motorcycle": 20, "van": 80, "truck": 200}
    
    # Depot location (Central Jakarta)
    depot_lat = -6.2088
    depot_lon = 106.8456
    
    vehicles = []
    for i in range(count):
        v_type = random.choice(vehicle_types)
        vehicles.append({
            "vehicle_id": f"V{str(i+1).zfill(3)}",
            "vehicle_type": v_type,
            "capacity": capacities[v_type],
            "driver_name": f"Driver {chr(65+i)}",
            "start_lat": depot_lat,
            "start_lon": depot_lon,
        })
    
    return vehicles


async def seed_database():
    """Seed the database with sample data."""
    import httpx
    
    base_url = "http://localhost:8000/api/v1"
    
    print("Generating sample data...")
    
    # Generate packages
    packages = [generate_package(i) for i in range(1, 51)]
    
    print(f"Generated {len(packages)} packages")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Ingest packages
        success_count = 0
        for pkg in packages:
            try:
                response = await client.post(
                    f"{base_url}/ingest/ocr-text",
                    json={
                        "device_id": pkg["device_id"],
                        "package_id": pkg["package_id"],
                        "ocr_text": pkg["ocr_text"],
                        "ocr_confidence": pkg["ocr_confidence"],
                        "gps": pkg["gps"],
                        "priority": pkg["priority"],
                    }
                )
                
                if response.status_code == 200:
                    success_count += 1
                    result = response.json()
                    print(f"✓ {pkg['package_id']}: {result['status']}")
                else:
                    print(f"✗ {pkg['package_id']}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"✗ {pkg['package_id']}: Error - {e}")
        
        print(f"\nIngested {success_count}/{len(packages)} packages")
        
        # Run route optimization
        print("\nRunning route optimization...")
        try:
            response = await client.post(
                f"{base_url}/routes/optimize",
                json={
                    "planned_date": datetime.now().strftime("%Y-%m-%d"),
                    "max_solve_time_seconds": 60,
                    "balance_routes": True,
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Optimization complete!")
                print(f"  - Routes: {result['total_vehicles_used']}")
                print(f"  - Packages routed: {result['total_packages']}")
                print(f"  - Total distance: {result['total_distance_km']:.1f} km")
                print(f"  - Solve time: {result['optimization_time_ms']} ms")
                
                if result['unassigned_packages']:
                    print(f"  - Unassigned: {len(result['unassigned_packages'])}")
            else:
                print(f"✗ Optimization failed: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Optimization error: {e}")


def main():
    """Generate sample data files."""
    print("Generating sample data files...")
    
    # Generate packages
    packages = [generate_package(i) for i in range(1, 101)]
    
    with open("sample_packages.json", "w") as f:
        json.dump(packages, f, indent=2)
    print(f"Generated {len(packages)} packages -> sample_packages.json")
    
    # Generate vehicles
    vehicles = generate_vehicles(5)
    
    with open("sample_vehicles.json", "w") as f:
        json.dump(vehicles, f, indent=2)
    print(f"Generated {len(vehicles)} vehicles -> sample_vehicles.json")
    
    # Print sample for inspection
    print("\nSample package:")
    print(json.dumps(packages[0], indent=2))


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--seed":
        # Seed database via API
        asyncio.run(seed_database())
    else:
        # Just generate files
        main()
