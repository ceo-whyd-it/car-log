#!/bin/bash
set -e

echo "========================================="
echo "  Car Log MCP Servers - Starting..."
echo "========================================="

# Function to start a server and log its status
start_server() {
    local server_name=$1
    local server_module=$2

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting ${server_name}..."
    python -m "mcp_servers.${server_module}" &

    # Store PID
    eval "${server_name}_PID=$!"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ ${server_name} started (PID: $!)"
}

# Start all Python MCP servers in background
start_server "car-log-core" "car_log_core"
start_server "trip-reconstructor" "trip_reconstructor"
start_server "validation" "validation"
start_server "ekasa-api" "ekasa_api"
start_server "dashboard-ocr" "dashboard_ocr"
start_server "report-generator" "report_generator"

echo "========================================="
echo "  All Python MCP servers started"
echo "========================================="
echo ""
echo "Container is running. Logs will appear below:"
echo ""

# Function to handle shutdown
shutdown() {
    echo ""
    echo "========================================="
    echo "  Shutting down MCP servers..."
    echo "========================================="
    kill $car_log_core_PID $trip_reconstructor_PID $validation_PID \
         $ekasa_api_PID $dashboard_ocr_PID $report_generator_PID 2>/dev/null || true
    exit 0
}

# Trap SIGTERM and SIGINT
trap shutdown SIGTERM SIGINT

# Wait for all background processes
wait
