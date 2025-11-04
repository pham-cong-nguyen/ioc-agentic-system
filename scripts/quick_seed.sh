#!/bin/bash
# Quick script to add sample functions via API

BASE_URL="http://localhost:8862/api/v1/registry"

echo "🌱 Adding sample functions to the registry..."

# Function 1: IP Reputation Check
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "analyze_ip_reputation",
    "name": "Analyze IP Reputation",
    "description": "Check IP address reputation across threat intelligence sources",
    "domain": "security",
    "endpoint": "/api/security/ip/reputation",
    "method": "POST",
    "auth_required": true,
    "tags": ["security", "ip", "threat-intel"],
    "timeout": 30
  }' > /dev/null && echo "✅ Added: Analyze IP Reputation"

# Function 2: File Hash Analysis  
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "analyze_file_hash",
    "name": "Analyze File Hash",
    "description": "Check file hash against malware databases",
    "domain": "security",
    "endpoint": "/api/security/hash/analyze",
    "method": "POST",
    "auth_required": true,
    "tags": ["security", "hash", "malware"],
    "timeout": 45
  }' > /dev/null && echo "✅ Added: Analyze File Hash"

# Function 3: Domain Reputation
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "check_domain_reputation",
    "name": "Check Domain Reputation",
    "description": "Analyze domain reputation and DNS records",
    "domain": "security",
    "endpoint": "/api/security/domain/check",
    "method": "GET",
    "auth_required": true,
    "tags": ["security", "domain", "dns"],
    "timeout": 20
  }' > /dev/null && echo "✅ Added: Check Domain Reputation"

# Function 4: Network Traffic Analysis
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "analyze_network_traffic",
    "name": "Analyze Network Traffic",
    "description": "Analyze network traffic patterns for threats",
    "domain": "analytics",
    "endpoint": "/api/network/analyze",
    "method": "POST",
    "auth_required": true,
    "tags": ["network", "traffic", "analysis"],
    "timeout": 120
  }' > /dev/null && echo "✅ Added: Analyze Network Traffic"

# Function 5: IP Geolocation
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "geolocate_ip",
    "name": "Geolocate IP Address",
    "description": "Get geographic location for an IP address",
    "domain": "analytics",
    "endpoint": "/api/network/geoip",
    "method": "GET",
    "auth_required": false,
    "tags": ["network", "geolocation", "ip"],
    "cache_ttl": 86400,
    "timeout": 5
  }' > /dev/null && echo "✅ Added: Geolocate IP"

# Function 6: Energy Consumption Monitor
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "monitor_energy_usage",
    "name": "Monitor Energy Usage",
    "description": "Track and analyze energy consumption data",
    "domain": "energy",
    "endpoint": "/api/energy/monitor",
    "method": "GET",
    "auth_required": true,
    "tags": ["energy", "monitoring", "consumption"],
    "timeout": 15
  }' > /dev/null && echo "✅ Added: Monitor Energy Usage"

# Function 7: Traffic Flow Analysis
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "analyze_traffic_flow",
    "name": "Analyze Traffic Flow",
    "description": "Analyze city traffic patterns and congestion",
    "domain": "traffic",
    "endpoint": "/api/traffic/analyze",
    "method": "POST",
    "auth_required": true,
    "tags": ["traffic", "transportation", "analysis"],
    "timeout": 30
  }' > /dev/null && echo "✅ Added: Analyze Traffic Flow"

# Function 8: Air Quality Monitor
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "monitor_air_quality",
    "name": "Monitor Air Quality",
    "description": "Track air quality metrics and pollution levels",
    "domain": "environment",
    "endpoint": "/api/environment/air-quality",
    "method": "GET",
    "auth_required": false,
    "tags": ["environment", "air-quality", "monitoring"],
    "cache_ttl": 1800,
    "timeout": 10
  }' > /dev/null && echo "✅ Added: Monitor Air Quality"

# Function 9: Health Data Analytics
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "analyze_health_data",
    "name": "Analyze Health Data",
    "description": "Analyze population health metrics and trends",
    "domain": "health",
    "endpoint": "/api/health/analytics",
    "method": "POST",
    "auth_required": true,
    "tags": ["health", "analytics", "population"],
    "timeout": 45
  }' > /dev/null && echo "✅ Added: Analyze Health Data"

# Function 10: Data Visualization
curl -s -X POST "$BASE_URL/functions" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "generate_visualization",
    "name": "Generate Data Visualization",
    "description": "Create charts and graphs from data",
    "domain": "analytics",
    "endpoint": "/api/analytics/visualize",
    "method": "POST",
    "auth_required": true,
    "tags": ["analytics", "visualization", "charts"],
    "timeout": 20
  }' > /dev/null && echo "✅ Added: Generate Visualization"

echo ""
echo "============================================================"
echo "📊 Seeding complete! Added 10 sample functions."
echo "============================================================"
echo ""
echo "🔍 View functions at: http://localhost:8862/#registry"
echo "📚 API docs at: http://localhost:8862/api/v1/docs"
