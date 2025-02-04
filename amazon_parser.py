#!/usr/bin/env python3

import logging
import re
from typing import Dict, Optional, List, Any, Union
from bs4 import BeautifulSoup
import pymongo
from dataclasses import dataclass, asdict
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='laptop_parser.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('laptop_parser')

@dataclass
class GPUInfo:
    brand: Optional[str] = None
    series: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[str] = None

@dataclass
class CPUInfo:
    brand: Optional[str] = None
    series: Optional[str] = None
    generation: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[str] = None

@dataclass
class ProcessingStats:
    total_documents: int = 0
    successful_processing: int = 0
    failed_processing: int = 0
    inserted_documents: int = 0
    gpu_conflicts: int = 0
    cpu_conflicts: int = 0

class SpecificationParser:
    """Parser for laptop specifications with enhanced GPU and CPU detection"""
    
    def __init__(self):
        # NVIDIA GPU patterns
        self.nvidia_patterns = [
            r'(nvidia|geforce)\s*(rtx|gtx)\s*(40|30|20|16|10)(\d{2})\s*(ti|super)?',
            r'(nvidia|geforce|rtx|gtx)\s*(rtx|gtx)?\s*(40|30|20|16|10)(\d{2})\s*(ti|super)?'
        ]
        
        # AMD GPU patterns
        self.amd_gpu_patterns = [
            r'amd\s*(radeon)?\s*(rx)\s*(7|6|5|4)(\d{3})\s*(xt)?',
            r'(radeon|amd)?\s*(rx)?\s*(7|6|5|4)(\d{3})\s*(xt)?'
        ]
        
        # Intel GPU patterns
        self.intel_gpu_patterns = [
            # Arc series
            r'(intel)?\s*arc\s*[ab]?(3|5|7)(\d{2})',
            r'(intel)?\s*arc\s*(a|b)?(\d{3})',
            # Iris series
            r'(intel)?\s*iris\s*(xe(\s*max)?|pro|plus)?',
            r'(intel)?\s*iris\s*xe\s*graphics',
            # UHD/HD series
            r'(intel)?\s*(uhd|hd)\s*graphics\s*(\d{3,4})?'
        ]
        
        # CPU patterns
        self.intel_cpu_patterns = [
            r'(intel)?\s*(core)?\s*(ultra|i[3579])\s*-?\s*(\d{1,2})(\d{3})[HKF]?[HKF]?\s*(h|u|hx|k)?',
            r'(intel)?\s*(core)?\s*(i[3579])\s*-?\s*(\d{1,2})th\s*gen'
        ]
        self.amd_cpu_patterns = [
            r'(amd)?\s*(ryzen)\s*([3579])\s*(\d{4})[HUX]?\s*(h|u|hx)?',
            r'(amd)?\s*(ryzen)\s*([3579])\s*-?\s*(\d{4,5})[HUX]?\s*(h|u|hx)?'
        ]

    def parse_gpu_from_text(self, text: str, is_technical_detail: bool = False) -> GPUInfo:
        """Parse GPU information from text with enhanced Intel GPU support"""
        if not text:
            return GPUInfo()
            
        text = text.lower().strip()
        gpu_info = GPUInfo(
            source='technical_detail' if is_technical_detail else 'title',
            confidence='high' if is_technical_detail else 'low'
        )

        # Try NVIDIA patterns first
        for pattern in self.nvidia_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gpu_info.brand = 'NVIDIA'
                groups = match.groups()
                
                if 'rtx' in text:
                    gpu_info.series = 'RTX'
                elif 'gtx' in text:
                    gpu_info.series = 'GTX'
                
                series_num = next((g for g in groups if g in ['40', '30', '20', '16', '10']), '')
                model_num = next((g for g in groups if re.match(r'\d{2}$', str(g))), '')
                if series_num and model_num:
                    gpu_info.model = f"{series_num}{model_num}"
                
                if 'ti' in text:
                    gpu_info.variant = 'Ti'
                elif 'super' in text:
                    gpu_info.variant = 'SUPER'
                return gpu_info

        # Try Intel patterns before AMD
        for pattern in self.intel_gpu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gpu_info.brand = 'Intel'
                
                # Handle Arc series
                if 'arc' in text:
                    gpu_info.series = 'Arc'
                    arc_match = re.search(r'(a|b)?(\d{3})', text)
                    if arc_match:
                        prefix, number = arc_match.groups()
                        if prefix:
                            gpu_info.model = f"{prefix.upper()}{number}"
                        else:
                            gpu_info.model = number
                
                # Handle Iris series
                elif 'iris' in text:
                    gpu_info.series = 'Iris'
                    if 'xe max' in text:
                        gpu_info.variant = 'Xe MAX'
                    elif 'xe' in text:
                        gpu_info.variant = 'Xe'
                    elif 'pro' in text:
                        gpu_info.variant = 'Pro'
                    elif 'plus' in text:
                        gpu_info.variant = 'Plus'
                
                # Handle UHD/HD Graphics
                elif 'uhd' in text or 'hd' in text:
                    gpu_info.series = 'UHD' if 'uhd' in text else 'HD'
                    model_match = re.search(r'(\d{3,4})', text)
                    if model_match:
                        gpu_info.model = model_match.group(1)
                
                return gpu_info

        # Try AMD patterns last
        for pattern in self.amd_gpu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gpu_info.brand = 'AMD'
                gpu_info.series = 'RX'
                groups = match.groups()
                
                series_num = next((g for g in groups if g in ['7', '6', '5', '4']), '')
                model_num = next((g for g in groups if re.match(r'\d{3}$', str(g))), '')
                if series_num and model_num:
                    gpu_info.model = f"{series_num}{model_num}"
                
                if 'xt' in text:
                    gpu_info.variant = 'XT'
                return gpu_info

        return gpu_info

    def parse_cpu_from_text(self, text: str, is_technical_detail: bool = False) -> CPUInfo:
        """Parse CPU information from text"""
        if not text:
            return CPUInfo()
            
        text = text.lower().strip()
        cpu_info = CPUInfo(
            source='technical_detail' if is_technical_detail else 'title',
            confidence='high' if is_technical_detail else 'low'
        )

        # Try Intel patterns first
        for pattern in self.intel_cpu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cpu_info.brand = 'Intel'
                groups = match.groups()
                
                series = next((g for g in groups if g in ['ultra', 'i3', 'i5', 'i7', 'i9']), '')
                cpu_info.series = series.upper() if series else None
                
                gen = next((g for g in groups if re.match(r'\d{1,2}', str(g))), '')
                if gen:
                    cpu_info.generation = f"{gen}th Gen"
                
                model = next((g for g in groups if re.match(r'\d{3,4}', str(g))), '')
                if model:
                    cpu_info.model = model
                
                variant = next((g for g in groups if g in ['h', 'u', 'hx', 'k']), None)
                if variant:
                    cpu_info.variant = variant.upper()
                return cpu_info

        # Try AMD patterns
        for pattern in self.amd_cpu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cpu_info.brand = 'AMD'
                groups = match.groups()
                
                if 'ryzen' in text:
                    ryzen_num = next((g for g in groups if g in ['3', '5', '7', '9']), '')
                    cpu_info.series = f"Ryzen {ryzen_num}"
                
                model = next((g for g in groups if re.match(r'\d{4,5}', str(g))), '')
                if model:
                    cpu_info.model = model
                    gen_num = model[0]
                    cpu_info.generation = f"Gen {gen_num}"
                
                variant = next((g for g in groups if g in ['h', 'u', 'hx']), None)
                if variant:
                    cpu_info.variant = variant.upper()
                return cpu_info

        return cpu_info

class AmazonParser:
    """Main parser class for Amazon laptop pages"""
    
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        try:
            self.client = pymongo.MongoClient(mongo_uri)
            # Verify connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            self.source_db = self.client["raw_laptop_data"]
            self.dest_db = self.client["laptop_data"]
            
            # Verify databases and collections
            raw_docs_count = self.source_db.raw_pages.count_documents({})
            logger.info(f"Found {raw_docs_count} documents in source database")
            
            if raw_docs_count == 0:
                logger.warning("No documents found in source database!")
            
            self.spec_parser = SpecificationParser()
            self.stats = ProcessingStats()
            
        except Exception as e:
            logger.error(f"MongoDB Connection Error: {str(e)}")
            raise

    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product title from the page"""
        title_element = soup.find('span', {'id': 'productTitle'})
        return title_element.text.strip() if title_element else None

    def extract_price_info(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """Extract price information from the page"""
        price_info = {
            "current_price": None,
            "mrp": None,
            "discount_percentage": None
        }
        
        try:
            # Extract current price
            price_element = soup.find('span', {'class': 'a-price-whole'})
            if price_element:
                price_text = price_element.text.strip().replace(',', '')
                price_info["current_price"] = float(price_text)

            # Extract MRP
            mrp_element = soup.find('span', {'class': 'a-price a-text-price'})
            if mrp_element:
                mrp_text = mrp_element.find('span', {'class': 'a-offscreen'})
                if mrp_text:
                    mrp = mrp_text.text.strip().replace('₹', '').replace(',', '')
                    price_info["mrp"] = float(mrp)

            # Extract discount
            discount_element = soup.find('span', {'class': 'savingPriceOverride'})
            if discount_element:
                discount = discount_element.text.strip().replace('-', '').replace('%', '')
                price_info["discount_percentage"] = float(discount)

        except ValueError as e:
            logger.error(f"Error parsing price values: {str(e)}")
        
        return price_info

    def parse_technical_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract technical details from the page"""
        tech_details = {}
        table = soup.find('table', {'id': 'productDetails_techSpec_section_1'})
        
        if table:
            rows = table.find_all('tr')
            for row in rows:
                label = row.find('th')
                value = row.find('td')
                if label and value:
                    key = label.text.strip().replace('\u200e', '').strip()
                    val = value.text.strip().replace('\u200e', '').strip()
                    tech_details[key] = val

        return tech_details

    def standardize_specs(self, tech_details: Dict[str, str], title: str) -> Dict[str, Any]:
        """Standardize and validate specifications"""
        # Extract GPU and CPU information
        tech_gpu = self.spec_parser.parse_gpu_from_text(
            tech_details.get("Graphics Card Description", ""),
            is_technical_detail=True
        )
        title_gpu = self.spec_parser.parse_gpu_from_text(title)

        tech_cpu = self.spec_parser.parse_cpu_from_text(
            tech_details.get("Processor Type", ""),
            is_technical_detail=True
        )
        title_cpu = self.spec_parser.parse_cpu_from_text(title)

        # Initialize conflicts list
        conflicts = []

        # Validate GPU information
        final_gpu = asdict(tech_gpu if tech_gpu.brand else title_gpu)
        if tech_gpu.brand and title_gpu.brand and tech_gpu.brand != title_gpu.brand:
            conflicts.append({
                'component': 'GPU',
                'field': 'brand',
                'tech_value': tech_gpu.brand,
                'title_value': title_gpu.brand,
                'resolution': f'Used technical detail value: {tech_gpu.brand}'
            })
            self.stats.gpu_conflicts += 1

        # Validate CPU information
        final_cpu = asdict(tech_cpu if tech_cpu.brand else title_cpu)
        if tech_cpu.brand and title_cpu.brand and tech_cpu.brand != title_cpu.brand:
            conflicts.append({
                'component': 'CPU',
                'field': 'brand',
                'tech_value': tech_cpu.brand,
                'title_value': title_cpu.brand,
                'resolution': f'Used technical detail value: {tech_cpu.brand}'
            })
            self.stats.cpu_conflicts += 1

        # Create standardized specifications
        specs = {
            "brand": tech_details.get("Brand"),
            "model": tech_details.get("Item model number"),
            "series": tech_details.get("Series"),
            "processor": final_cpu,
            "graphics": final_gpu,
            "memory": {
                "ram_size": self.normalize_ram_size(tech_details.get("RAM Size")),
                "technology": tech_details.get("Memory Technology"),
                "max_supported": tech_details.get("Maximum Memory Supported")
            },
            "storage": {
                "size": tech_details.get("Hard Drive Size"),
                "type": tech_details.get("Hard Disk Description"),
                "interface": tech_details.get("Hard Drive Interface")
            },
            "display": {
                "size": self.normalize_display_size(tech_details.get("Standing screen display size")),
                "resolution": tech_details.get("Screen Resolution")
            },
            "operating_system": tech_details.get("Operating System"),
            "battery": {
                "life": self.normalize_battery_life(tech_details.get("Average Battery Life (in hours)")),
                "cells": tech_details.get("Number of Lithium Ion Cells"),
                "energy_content": tech_details.get("Lithium Battery Energy Content")
            },
            "physical": {
                "dimensions": tech_details.get("Product Dimensions"),
                "weight": self.normalize_weight(tech_details.get("Item Weight")),
                "color": tech_details.get("Colour")
            },
            "connectivity": {
                "type": tech_details.get("Connectivity Type"),
                "usb2_ports": self.normalize_port_count(tech_details.get("Number of USB 2.0 Ports")),
                "usb3_ports": self.normalize_port_count(tech_details.get("Number of USB 3.0 Ports"))
            },
            "included_components": tech_details.get("Included Components")
        }

        if conflicts:
            specs["specification_conflicts"] = conflicts

        return specs

    def normalize_ram_size(self, ram_size: Optional[str]) -> Optional[float]:
        """Convert RAM size to GB"""
        if not ram_size:
            return None
        try:
            match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB|TB)?', ram_size, re.IGNORECASE)
            if match:
                size, unit = match.groups()
                size = float(size)
                if unit:
                    unit = unit.upper()
                    if unit == 'MB':
                        size /= 1024
                    elif unit == 'TB':
                        size *= 1024
                return size
        except Exception as e:
            logger.error(f"Error normalizing RAM size '{ram_size}': {str(e)}")
        return None

    def normalize_display_size(self, display_size: Optional[str]) -> Optional[float]:
        """Convert display size to inches"""
        if not display_size:
            return None
        try:
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:inches|")?', display_size, re.IGNORECASE)
            if match:
                return float(match.group(1))
        except Exception as e:
            logger.error(f"Error normalizing display size '{display_size}': {str(e)}")
        return None

    def normalize_battery_life(self, battery_life: Optional[str]) -> Optional[float]:
        """Convert battery life to hours"""
        if not battery_life:
            return None
        try:
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours|hrs?)?', battery_life, re.IGNORECASE)
            if match:
                return float(match.group(1))
        except Exception as e:
            logger.error(f"Error normalizing battery life '{battery_life}': {str(e)}")
        return None

    def normalize_weight(self, weight: Optional[str]) -> Optional[float]:
        """Convert weight to kg"""
        if not weight:
            return None
        try:
            match = re.search(r'(\d+(?:\.\d+)?)\s*(kg|g|kilograms|grams)?', weight, re.IGNORECASE)
            if match:
                value, unit = match.groups()
                value = float(value)
                if unit and unit.lower() in ['g', 'grams']:
                    value /= 1000
                return value
        except Exception as e:
            logger.error(f"Error normalizing weight '{weight}': {str(e)}")
        return None

    def normalize_port_count(self, port_count: Optional[str]) -> Optional[int]:
        """Convert port count to integer"""
        if not port_count:
            return None
        try:
            match = re.search(r'(\d+)', port_count)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.error(f"Error normalizing port count '{port_count}': {str(e)}")
        return None

    def process_html_documents(self) -> ProcessingStats:
        """Main processing function"""
        raw_collection = self.source_db["raw_pages"]
        laptop_collection = self.dest_db["laptop_specs"]
        
        try:
            # Drop existing collection
            laptop_collection.drop()
            logger.info("Dropped existing collection")

            for doc in raw_collection.find():
                try:
                    self.stats.total_documents += 1
                    
                    # Get HTML content
                    html_content = doc.get('content', doc.get('html_content', doc.get('source', doc.get('html'))))
                    if not html_content:
                        logger.warning(f"No HTML content found in document {doc['_id']}")
                        self.stats.failed_processing += 1
                        continue

                    # Parse HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract information
                    title = self.extract_title(soup)
                    price_info = self.extract_price_info(soup)
                    tech_details = self.parse_technical_details(soup)
                    specs = self.standardize_specs(tech_details, title)

                    # Create document
                    laptop_doc = {
                        "source_id": doc["_id"],
                        "url": doc.get("url", ""),
                        "title": title,
                        "pricing": price_info,
                        "specifications": specs,
                        "raw_specs": tech_details,
                        "processed_at": datetime.utcnow(),
                        "parser_version": "2.1.0"  # Updated version number
                    }

                    # Insert document and verify insertion
                    result = laptop_collection.insert_one(laptop_doc)
                    if result.inserted_id:
                        self.stats.successful_processing += 1
                        self.stats.inserted_documents += 1
                        logger.info(f"Successfully processed and inserted document {doc['_id']}")
                        
                        # Verify the document exists
                        inserted_doc = laptop_collection.find_one({"_id": result.inserted_id})
                        if not inserted_doc:
                            logger.warning(f"Document {doc['_id']} was inserted but couldn't be verified")
                    else:
                        logger.warning(f"Document {doc['_id']} may not have been inserted properly")
                        self.stats.failed_processing += 1

                except Exception as e:
                    self.stats.failed_processing += 1
                    logger.error(f"Error processing document {doc['_id']}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Fatal error in processing: {str(e)}")
            raise

        finally:
            # Log final statistics
            logger.info("Processing completed with following statistics:")
            logger.info(f"Total documents processed: {self.stats.total_documents}")
            logger.info(f"Successfully processed: {self.stats.successful_processing}")
            logger.info(f"Failed processing: {self.stats.failed_processing}")
            logger.info(f"Documents inserted: {self.stats.inserted_documents}")
            logger.info(f"GPU conflicts found: {self.stats.gpu_conflicts}")
            logger.info(f"CPU conflicts found: {self.stats.cpu_conflicts}")
            
            # Verify final collection state
            final_count = laptop_collection.count_documents({})
            logger.info(f"Final document count in collection: {final_count}")
            
            if final_count != self.stats.inserted_documents:
                logger.warning(f"Mismatch in document counts: Expected {self.stats.inserted_documents}, Found {final_count}")
                
            return self.stats

def verify_database_operation(stats: ProcessingStats):
    """Print processing statistics"""
    print("\nProcessing Statistics:")
    print(f"Total documents processed: {stats.total_documents}")
    print(f"Successfully processed: {stats.successful_processing}")
    print(f"Failed processing: {stats.failed_processing}")
    print(f"Documents inserted: {stats.inserted_documents}")
    print(f"GPU conflicts found: {stats.gpu_conflicts}")
    print(f"CPU conflicts found: {stats.cpu_conflicts}")

def main():
    """Main entry point"""
    try:
        parser = AmazonParser()
        stats = parser.process_html_documents()
        verify_database_operation(stats)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()