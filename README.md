# Paket - Package Routing & OCR System

A comprehensive system for package delivery routing with OCR-based address extraction, normalization, geocoding, and VRP (Vehicle Routing Problem) optimization.

## 🚀 Features

- **OCR Processing**: Server-side OCR using Tesseract for package label extraction
- **Address Parsing**: Indonesian address parser with RT/RW support and OCR error correction
- **Geocoding**: Address geocoding with Nominatim (OSM) and Redis caching
- **VRP Optimization**: Route optimization using Google OR-Tools (CVRPTW)
- **Real-time Processing**: Kafka-based message streaming for async processing
- **RESTful API**: FastAPI-based endpoints for all operations

## 📋Requirements

- Docker & Docker Compose
- Python 3.11+ (for local development)
- 4GB+ RAM (for all services)

## 🏃 Quick Start

### 1. Clone and Configure

```bash
cd paket
cp .env.example .env
# Edit .env with your configurations
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL + PostGIS (port 5432)
- Redis (port 6379)
- Kafka + Zookeeper (port 29092)
- API Service (port 8000)
- Background Worker

### 3. Verify Services

```bash
# Check health
curl http://localhost:8000/health

# Check readiness (all dependencies)
curl http://localhost:8000/health/ready
```

### 4. Access API Documentation

Open [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.

## 📡 API Endpoints

### Ingest

```bash
# Ingest OCR text from device
POST /api/v1/ingest/ocr-text
{
  "device_id": "scanner-01",
  "package_id": "PKT2025123456",
  "ocr_text": "Jalan Merdeka 45 RT 02/RW 03, Kebayoran Lama, Jakarta Selatan 12220",
  "ocr_confidence": 0.85,
  "priority": "standard"
}

# Upload image for server-side OCR
POST /api/v1/ingest/image
(multipart form with image file)
```

### Address

```bash
# Parse address
POST /api/v1/address/parse
{
  "raw_text": "Jln Sudirman No.123, Menteng, Jakpus 10110"
}

# Geocode address
POST /api/v1/address/geocode
{
  "address": {
    "street": "Jalan Sudirman",
    "house_number": "123",
    "subdistrict": "Menteng",
    "city": "Jakarta Pusat"
  }
}
```

### Routing

```bash
# Optimize routes
POST /api/v1/routes/optimize
{
  "planned_date": "2025-12-12",
  "max_solve_time_seconds": 120,
  "balance_routes": true
}

# Get route details
GET /api/v1/routes/{route_id}

# List routes
GET /api/v1/routes?planned_date=2025-12-12
```

## 🧪 Testing with Sample Data

Generate and seed sample data:

```bash
# Generate sample files
python scripts/seed_data.py

# Seed via API (requires running services)
python scripts/seed_data.py --seed
```

## 🏗️ Project Structure

```
paket/
├── docker-compose.yml      # All services orchestration
├── .env.example            # Environment template
├── scripts/
│   ├── init_db.sql        # Database schema
│   └── seed_data.py       # Sample data generator
└── services/
    └── api/
        ├── Dockerfile
        ├── requirements.txt
        ├── main.py          # FastAPI application
        ├── config.py        # Settings management
        ├── models/          # Pydantic models
        ├── routers/         # API endpoints
        ├── services/        # Business logic
        │   ├── address_parser.py
        │   ├── geocoder.py
        │   ├── ocr_service.py
        │   └── vrp_optimizer.py
        ├── db/              # Database layer
        └── workers/         # Kafka consumers
```

## ⚙️ Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | `localhost:29092` |
| `GEOCODING_PROVIDER` | Geocoder to use | `nominatim` |
| `VRP_MAX_SOLVE_TIME_SECONDS` | Max optimization time | `300` |

## 🔧 Development

### Local Development (without Docker)

```bash
cd services/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn main:app --reload --port 8000
```

### Run Tests

```bash
pytest tests/ -v
```

## 📊 Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Device    │────▶│  API/Ingest │────▶│    Kafka    │
│  (Scanner)  │     │   Gateway   │     │   Broker    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          ▼                          │
              ┌─────┴─────┐           ┌─────────────┐           ┌─────────┴─────┐
              │   OCR     │           │   Address   │           │   Geocoder    │
              │  Service  │──────────▶│   Parser    │──────────▶│   + Cache     │
              └───────────┘           └─────────────┘           └───────────────┘
                                               │
                                               ▼
                                      ┌─────────────┐
                                      │     VRP     │
                                      │  Optimizer  │
                                      └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          ▼                          │
              ┌─────┴─────┐           ┌─────────────┐           ┌─────────┴─────┐
              │ PostgreSQL│           │    Redis    │           │  Driver App   │
              │ + PostGIS │           │    Cache    │           │   (Future)    │
              └───────────┘           └─────────────┘           └───────────────┘
```

## 📱 Client Applications

### Web Dashboard (Next.js)

Admin dashboard for package management, route visualization, and address verification.

```bash
cd clients/web
npm install
npm run dev
# Open http://localhost:3000
```

**Features:**
- 📊 Real-time stats and metrics
- 🗺️ Route visualization with Leaflet maps
- 📦 Package management with search/filter
- ✅ Human-in-the-loop verification
- 🚀 VRP optimization trigger

### Scanner App (Flutter)

Mobile app for warehouse staff to scan package labels and extract addresses.

```bash
cd clients/scanner
flutter pub get
flutter run
```

**Features:**
- 📷 Camera-based label scanning
- 🔤 On-device OCR with ML Kit
- 📍 GPS location capture
- 🔄 Offline-first with sync queue
- 📜 Scan history

### Driver App (Flutter)

Mobile app for delivery drivers to navigate routes and confirm deliveries.

```bash
cd clients/driver
flutter pub get
flutter run
```

**Features:**
- 🗺️ Interactive route map
- 📍 Turn-by-turn navigation (Google Maps integration)
- ✅ Delivery confirmation
- ⏭️ Skip with reason tracking
- 📊 Progress tracking

## 🚧 Roadmap

- [ ] ETA prediction ML model
- [ ] Real-time traffic integration
- [ ] Demand forecasting
- [ ] A/B testing framework
- [ ] Push notifications for drivers
- [ ] Customer delivery tracking

## 📄 License

MIT License
