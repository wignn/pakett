"""
Kafka workers for background processing.
Handles asynchronous processing of packages through the pipeline.
"""

import json
import logging
import asyncio
from typing import Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from config import settings
from db.database import async_session_maker
from db.repositories import PackageRepository, AddressRepository
from services.address_parser import get_address_parser
from services.geocoder import get_geocoder

logger = logging.getLogger(__name__)


class PackageProcessor:
    """
    Kafka consumer for processing packages.
    
    Listens to the ingest topic and processes packages through:
    1. Address parsing
    2. Geocoding
    3. Status updates
    """
    
    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[AIOKafkaProducer] = None
        self.running = False
    
    async def start(self):
        """Start the Kafka consumer."""
        logger.info("Starting package processor worker...")
        
        self.consumer = AIOKafkaConsumer(
            settings.kafka_topics_ingest,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        
        await self.consumer.start()
        await self.producer.start()
        
        self.running = True
        logger.info(f"Package processor started, listening to {settings.kafka_topics_ingest}")
    
    async def stop(self):
        """Stop the Kafka consumer."""
        self.running = False
        
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
        
        logger.info("Package processor stopped")
    
    async def process_message(self, message: dict):
        """
        Process a single package message.
        
        Message format:
        {
            "package_id": "UUID",
            "action": "parse" | "geocode" | "full"
        }
        """
        package_id = message.get("package_id")
        action = message.get("action", "full")
        
        if not package_id:
            logger.warning("Received message without package_id")
            return
        
        logger.info(f"Processing package {package_id}, action: {action}")
        
        async with async_session_maker() as session:
            try:
                package_repo = PackageRepository(session)
                address_repo = AddressRepository(session)
                
                # Get package
                package = await package_repo.get_by_package_id(package_id)
                
                if not package:
                    logger.warning(f"Package {package_id} not found")
                    return
                
                if action in ("parse", "full"):
                    # Parse address
                    parser = get_address_parser()
                    parse_result = parser.parse(package["ocr_text"])
                    
                    logger.info(
                        f"Parsed {package_id}: confidence={parse_result.confidence:.2f}"
                    )
                
                if action in ("geocode", "full"):
                    # Get existing address
                    address = await address_repo.get_by_package_id(package["id"])
                    
                    if address and not address.get("lat"):
                        # Geocode
                        geocoder = get_geocoder()
                        parser = get_address_parser()
                        
                        # Build geocode query from stored address
                        from services.address_parser import ParseResult
                        parse_result = ParseResult(
                            street=address.get("street"),
                            house_number=address.get("house_number"),
                            subdistrict=address.get("subdistrict"),
                            city=address.get("city"),
                            postal_code=address.get("postal_code"),
                        )
                        
                        geocode_query = parser.format_for_geocoding(parse_result)
                        geocode_result = await geocoder.geocode(geocode_query)
                        
                        if geocode_result:
                            # Update address with coordinates
                            # (In a real implementation, we'd update the database)
                            logger.info(
                                f"Geocoded {package_id}: "
                                f"{geocode_result.lat}, {geocode_result.lon}"
                            )
                            
                            # Update package status
                            await package_repo.update_status(
                                package["id"],
                                "geocoded"
                            )
                
                await session.commit()
                
                # Publish completion event
                await self.producer.send_and_wait(
                    settings.kafka_topics_address,
                    {
                        "package_id": package_id,
                        "status": "processed",
                        "action": action
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to process package {package_id}: {e}")
                await session.rollback()
    
    async def run(self):
        """Main consumer loop."""
        await self.start()
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    await self.process_message(message.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        finally:
            await self.stop()


async def start_workers():
    """Start all Kafka workers."""
    processor = PackageProcessor()
    
    try:
        await processor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down workers...")
    finally:
        await processor.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(start_workers())
