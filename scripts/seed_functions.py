#!/usr/bin/env python3
"""
Seed script to populate the function registry with sample IOC and security functions
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.database import get_db_session
from backend.registry.service import FunctionRegistryService
from backend.registry.schemas import FunctionMetadataCreate, Domain


SAMPLE_FUNCTIONS = [
    # IOC Analysis Functions
    {
        "function_id": "analyze_ip_reputation",
        "name": "Analyze IP Reputation",
        "description": "Check IP address reputation across multiple threat intelligence sources",
        "domain": Domain.SECURITY,
        "endpoint": "/api/security/ip/reputation",
        "method": "POST",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "ip_address": {"type": "string", "description": "IP address to analyze"},
                "sources": {"type": "array", "items": {"type": "string"}, "description": "TI sources to query"}
            },
            "required": ["ip_address"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "ip": {"type": "string"},
                "reputation_score": {"type": "integer"},
                "is_malicious": {"type": "boolean"},
                "sources": {"type": "array"}
            }
        },
        "tags": ["ioc", "ip", "threat-intel", "reputation"],
        "rate_limit": 100,
        "cache_ttl": 3600,
        "timeout": 30
    },
    {
        "function_id": "analyze_file_hash",
        "name": "Analyze File Hash",
        "description": "Check file hash (MD5/SHA1/SHA256) against malware databases",
        "domain": Domain.SECURITY,
        "endpoint": "/api/security/hash/analyze",
        "method": "POST",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "hash": {"type": "string", "description": "File hash to analyze"},
                "hash_type": {"type": "string", "enum": ["md5", "sha1", "sha256"]},
                "detailed": {"type": "boolean", "default": False}
            },
            "required": ["hash"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "hash": {"type": "string"},
                "malicious": {"type": "boolean"},
                "detections": {"type": "integer"},
                "first_seen": {"type": "string"},
                "last_seen": {"type": "string"}
            }
        },
        "tags": ["ioc", "hash", "malware", "file-analysis"],
        "rate_limit": 50,
        "cache_ttl": 7200,
        "timeout": 45
    },
    {
        "function_id": "check_domain_reputation",
        "name": "Check Domain Reputation",
        "description": "Analyze domain reputation, DNS records, and associated threats",
        "domain": Domain.SECURITY,
        "endpoint": "/api/security/domain/check",
        "method": "GET",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name to check"},
                "include_whois": {"type": "boolean", "default": False},
                "include_dns": {"type": "boolean", "default": True}
            },
            "required": ["domain"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string"},
                "risk_score": {"type": "integer"},
                "category": {"type": "string"},
                "dns_records": {"type": "object"}
            }
        },
        "tags": ["ioc", "domain", "dns", "reputation"],
        "rate_limit": 100,
        "cache_ttl": 1800,
        "timeout": 20
    },
    
    {
        "function_id": "nguyenpc2",
        "name": "nguyenpc2 function",
        "description": "Analyze domain reputation, DNS records, and associated threats",
        "domain": Domain.SECURITY,
        "endpoint": "/api/security/domain/nguyenpc2_check",
        "method": "GET",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name to check"},
                "include_whois": {"type": "boolean", "default": False},
                "include_dns": {"type": "boolean", "default": True}
            },
            "required": ["domain"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string"},
                "risk_score": {"type": "integer"},
                "category": {"type": "string"},
                "dns_records": {"type": "object"}
            }
        },
        "tags": ["ioc", "domain", "dns", "reputation"],
        "rate_limit": 100,
        "cache_ttl": 1800,
        "timeout": 20
    },
    
    # Threat Intelligence Functions
    {
        "function_id": "query_threat_feed",
        "name": "Query Threat Intelligence Feed",
        "description": "Search threat intelligence feeds for indicators of compromise",
        "domain": Domain.SECURITY,
        "endpoint": "/api/threat/feed/query",
        "method": "POST",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "indicator": {"type": "string"},
                "indicator_type": {"type": "string", "enum": ["ip", "domain", "hash", "url"]},
                "feeds": {"type": "array", "items": {"type": "string"}},
                "timeframe": {"type": "string", "default": "24h"}
            },
            "required": ["indicator", "indicator_type"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "indicator": {"type": "string"},
                "matches": {"type": "array"},
                "threat_level": {"type": "string"},
                "recommendations": {"type": "array"}
            }
        },
        "tags": ["threat-intel", "feed", "ioc"],
        "rate_limit": 200,
        "cache_ttl": 600,
        "timeout": 60
    },
    {
        "function_id": "get_threat_actor_profile",
        "name": "Get Threat Actor Profile",
        "description": "Retrieve detailed profile of a known threat actor or APT group",
        "domain": Domain.SECURITY,
        "endpoint": "/api/threat/actor/{actor_id}",
        "method": "GET",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "actor_id": {"type": "string", "description": "Threat actor identifier"},
                "include_iocs": {"type": "boolean", "default": True},
                "include_ttps": {"type": "boolean", "default": True}
            },
            "required": ["actor_id"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "actor_id": {"type": "string"},
                "name": {"type": "string"},
                "aliases": {"type": "array"},
                "description": {"type": "string"},
                "ttps": {"type": "array"},
                "associated_iocs": {"type": "array"}
            }
        },
        "tags": ["threat-intel", "apt", "threat-actor"],
        "rate_limit": 50,
        "cache_ttl": 86400,
        "timeout": 30
    },
    
    # Alert Management Functions
    {
        "function_id": "create_security_alert",
        "name": "Create Security Alert",
        "description": "Create a new security alert in the SIEM system",
        "domain": Domain.SECURITY,
        "endpoint": "/api/alerts/create",
        "method": "POST",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "source": {"type": "string"},
                "indicators": {"type": "array"},
                "tags": {"type": "array"}
            },
            "required": ["title", "severity"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "alert_id": {"type": "string"},
                "created_at": {"type": "string"},
                "status": {"type": "string"}
            }
        },
        "tags": ["alerts", "siem", "incident"],
        "rate_limit": 100,
        "timeout": 15
    },
    {
        "function_id": "query_alerts",
        "name": "Query Security Alerts",
        "description": "Search and filter security alerts by various criteria",
        "domain": Domain.SECURITY,
        "endpoint": "/api/alerts/search",
        "method": "POST",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "severity": {"type": "array", "items": {"type": "string"}},
                "status": {"type": "array", "items": {"type": "string"}},
                "time_range": {"type": "object"},
                "tags": {"type": "array"},
                "limit": {"type": "integer", "default": 50}
            }
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "total": {"type": "integer"},
                "alerts": {"type": "array"},
                "facets": {"type": "object"}
            }
        },
        "tags": ["alerts", "search", "query"],
        "rate_limit": 200,
        "cache_ttl": 60,
        "timeout": 20
    },
    
    # Network Analysis Functions
    {
        "function_id": "analyze_network_traffic",
        "name": "Analyze Network Traffic",
        "description": "Analyze network traffic patterns for anomalies and threats",
        "domain": Domain.ANALYTICS,
        "endpoint": "/api/network/analyze",
        "method": "POST",
        "auth_required": True,
        "parameters": {
            "type": "object",
            "properties": {
                "pcap_file": {"type": "string", "description": "Base64 encoded PCAP"},
                "filters": {"type": "object"},
                "deep_inspection": {"type": "boolean", "default": False}
            },
            "required": ["pcap_file"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "analysis_id": {"type": "string"},
                "threats_detected": {"type": "integer"},
                "anomalies": {"type": "array"},
                "summary": {"type": "object"}
            }
        },
        "tags": ["network", "traffic", "pcap", "analysis"],
        "rate_limit": 20,
        "timeout": 120
    },
    {
        "function_id": "geolocate_ip",
        "name": "Geolocate IP Address",
        "description": "Get geographic location and network information for an IP address",
        "domain": Domain.ANALYTICS,
        "endpoint": "/api/network/geoip",
        "method": "GET",
        "auth_required": False,
        "parameters": {
            "type": "object",
            "properties": {
                "ip": {"type": "string", "description": "IP address to geolocate"},
                "detailed": {"type": "boolean", "default": False}
            },
            "required": ["ip"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "ip": {"type": "string"},
                "country": {"type": "string"},
                "city": {"type": "string"},
                "coordinates": {"type": "object"},
                "asn": {"type": "string"},
                "organization": {"type": "string"}
            }
        },
        "tags": ["network", "geolocation", "ip"],
        "rate_limit": 500,
        "cache_ttl": 86400,
        "timeout": 5
    },
    
    # General Utility Functions
    {
        "function_id": "decode_base64",
        "name": "Decode Base64",
        "description": "Decode Base64 encoded strings",
        "domain": Domain.ANALYTICS,
        "endpoint": "/api/utils/base64/decode",
        "method": "POST",
        "auth_required": False,
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Base64 encoded data"}
            },
            "required": ["data"]
        },
        "response_schema": {
            "type": "object",
            "properties": {
                "decoded": {"type": "string"},
                "format": {"type": "string"}
            }
        },
        "tags": ["utility", "encoding", "base64"],
        "rate_limit": 1000,
        "timeout": 2
    }
]


async def seed_database():
    """Seed the database with sample functions"""
    print("🌱 Starting database seeding...")
    
    async with get_db_session() as db:
        service = FunctionRegistryService(db)
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for func_data in SAMPLE_FUNCTIONS:
            try:
                # Check if function already exists
                existing = await service.get_function(func_data["function_id"])
                
                if existing:
                    print(f"⏭️  Skipping '{func_data['name']}' - already exists")
                    skipped_count += 1
                    continue
                
                # Create function
                function_create = FunctionMetadataCreate(**func_data)
                result = await service.create_function(function_create)
                
                print(f"✅ Created '{result.name}' ({result.function_id})")
                created_count += 1
                
            except Exception as e:
                print(f"❌ Error creating '{func_data['name']}': {e}")
                error_count += 1
        
        print("\n" + "="*60)
        print(f"📊 Seeding complete!")
        print(f"   ✅ Created: {created_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        print(f"   ❌ Errors:  {error_count}")
        print(f"   📦 Total:   {len(SAMPLE_FUNCTIONS)}")
        print("="*60)


async def clear_database():
    """Clear all functions from the database"""
    print("🗑️  Clearing all functions from database...")
    
    response = input("⚠️  Are you sure? This will delete ALL functions. Type 'yes' to confirm: ")
    
    if response.lower() != 'yes':
        print("❌ Aborted")
        return
    
    async with get_db_session() as db:
        service = FunctionRegistryService(db)
        
        # Get all functions
        functions, total = await service.list_functions(limit=1000)
        
        deleted_count = 0
        for func in functions:
            try:
                await service.delete_function(func.function_id)
                print(f"🗑️  Deleted '{func.name}'")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting '{func.name}': {e}")
        
        print(f"\n✅ Deleted {deleted_count} functions")


async def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        await clear_database()
    else:
        await seed_database()
    
    print("\n💡 Tip: Run with --clear flag to remove all functions before seeding")


if __name__ == "__main__":
    asyncio.run(main())
