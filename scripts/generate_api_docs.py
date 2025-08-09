#!/usr/bin/env python3
"""
Script to generate and aggregate OpenAPI documentation from all microservices
"""

import json
import asyncio
import httpx
import yaml
from pathlib import Path
from typing import Dict, Any, List


class APIDocumentationAggregator:
    """Aggregates OpenAPI documentation from multiple services"""
    
    def __init__(self):
        self.services = {
            "auth-service": {"url": "http://localhost:8005", "name": "Authentication Service"},
            "api-gateway": {"url": "http://localhost:8000", "name": "API Gateway"},
            "data-ingestion": {"url": "http://localhost:8001", "name": "Data Ingestion Service"},
            "data-processing": {"url": "http://localhost:8002", "name": "Data Processing Service"},
            "analytics": {"url": "http://localhost:8003", "name": "Analytics Service"},
            "notification": {"url": "http://localhost:8004", "name": "Notification Service"}
        }
        self.docs_dir = Path("docs/api")
        self.docs_dir.mkdir(exist_ok=True)
    
    async def fetch_openapi_spec(self, service_name: str, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Fetch OpenAPI specification from a service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{service_info['url']}/openapi.json")
                if response.status_code == 200:
                    spec = response.json()
                    # Add service-specific metadata
                    spec["info"]["x-service-name"] = service_name
                    spec["info"]["x-service-url"] = service_info["url"]
                    return spec
                else:
                    print(f"❌ Failed to fetch OpenAPI spec from {service_name}: HTTP {response.status_code}")
                    return None
        except Exception as e:
            print(f"❌ Error fetching OpenAPI spec from {service_name}: {e}")
            return None
    
    async def generate_service_docs(self):
        """Generate individual service documentation files"""
        print("🔄 Generating individual service documentation...")
        
        for service_name, service_info in self.services.items():
            print(f"  📡 Fetching {service_name}...")
            spec = await self.fetch_openapi_spec(service_name, service_info)
            
            if spec:
                # Save as JSON
                json_file = self.docs_dir / f"{service_name}.json"
                with open(json_file, 'w') as f:
                    json.dump(spec, f, indent=2)
                
                # Save as YAML
                yaml_file = self.docs_dir / f"{service_name}.yaml"
                with open(yaml_file, 'w') as f:
                    yaml.dump(spec, f, default_flow_style=False)
                
                print(f"  ✅ Generated documentation for {service_name}")
            else:
                print(f"  ⚠️  Skipped {service_name} (service not available)")
    
    async def generate_aggregated_spec(self):
        """Generate a single aggregated OpenAPI specification"""
        print("🔄 Generating aggregated API specification...")
        
        # Base specification
        aggregated_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Energy Tracking IoT Platform API",
                "description": "Aggregated API documentation for all microservices",
                "version": "1.0.0",
                "contact": {
                    "name": "Energy Tracking Platform",
                    "url": "https://github.com/alirizaadiyahsi/energy-tracking"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Development API Gateway"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            },
            "security": [{"bearerAuth": []}],
            "tags": []
        }
        
        # Collect all service specs
        for service_name, service_info in self.services.items():
            spec_file = self.docs_dir / f"{service_name}.json"
            if spec_file.exists():
                with open(spec_file, 'r') as f:
                    service_spec = json.load(f)
                
                # Add service tag
                service_tag = {
                    "name": service_name,
                    "description": service_spec.get("info", {}).get("description", "")
                }
                aggregated_spec["tags"].append(service_tag)
                
                # Merge paths (prefix with service name to avoid conflicts)
                for path, methods in service_spec.get("paths", {}).items():
                    # Skip health endpoints to avoid duplication
                    if path.startswith("/health"):
                        continue
                    
                    prefixed_path = f"/{service_name}{path}"
                    aggregated_spec["paths"][prefixed_path] = methods
                    
                    # Add service tag to all operations
                    for method_info in methods.values():
                        if isinstance(method_info, dict) and "tags" in method_info:
                            method_info["tags"] = [service_name] + method_info.get("tags", [])
                
                # Merge schemas
                components = service_spec.get("components", {})
                schemas = components.get("schemas", {})
                for schema_name, schema_def in schemas.items():
                    # Prefix schema names with service name to avoid conflicts
                    prefixed_name = f"{service_name.replace('-', '_').title()}{schema_name}"
                    aggregated_spec["components"]["schemas"][prefixed_name] = schema_def
        
        # Save aggregated specification
        aggregated_file = self.docs_dir / "aggregated.json"
        with open(aggregated_file, 'w') as f:
            json.dump(aggregated_spec, f, indent=2)
        
        aggregated_yaml_file = self.docs_dir / "aggregated.yaml"
        with open(aggregated_yaml_file, 'w') as f:
            yaml.dump(aggregated_spec, f, default_flow_style=False)
        
        print("✅ Generated aggregated API specification")
    
    def generate_postman_collection(self):
        """Generate Postman collection from aggregated spec"""
        print("🔄 Generating Postman collection...")
        
        # Basic Postman collection structure
        collection = {
            "info": {
                "name": "Energy Tracking IoT Platform",
                "description": "Postman collection for all microservices",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{jwt_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000",
                    "type": "string"
                },
                {
                    "key": "jwt_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # Add folders for each service
        for service_name, service_info in self.services.items():
            service_folder = {
                "name": service_name.replace('-', ' ').title(),
                "item": [],
                "description": f"Endpoints for {service_info['name']}"
            }
            
            # Add health check request
            health_request = {
                "name": "Health Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": f"{service_info['url']}/health",
                        "host": [service_info['url'].replace('http://', '').replace('https://', '')],
                        "path": ["health"]
                    }
                }
            }
            service_folder["item"].append(health_request)
            collection["item"].append(service_folder)
        
        # Save Postman collection
        postman_file = self.docs_dir / "postman_collection.json"
        with open(postman_file, 'w') as f:
            json.dump(collection, f, indent=2)
        
        print("✅ Generated Postman collection")
    
    async def run(self):
        """Run the documentation generation process"""
        print("🚀 Starting API documentation generation...")
        
        await self.generate_service_docs()
        await self.generate_aggregated_spec()
        self.generate_postman_collection()
        
        print("🎉 API documentation generation completed!")
        print(f"📁 Documentation saved in: {self.docs_dir.absolute()}")


if __name__ == "__main__":
    aggregator = APIDocumentationAggregator()
    asyncio.run(aggregator.run())
