#!/bin/bash
# correlate-logs.sh - Find all logs for a specific trace ID
#
# Usage: ./scripts/correlate-logs.sh <trace_id>
#
# This script helps debug issues by correlating logs across
# all Docker containers with a specific OpenTelemetry trace ID.

set -e

TRACE_ID=$1
MLFLOW_URL="${MLFLOW_URL:-http://localhost:5050}"

if [ -z "$TRACE_ID" ]; then
    echo "Usage: $0 <trace_id>"
    echo ""
    echo "Find all logs and traces for a specific trace ID."
    echo ""
    echo "Examples:"
    echo "  $0 abc123def456"
    echo "  $0 \$(docker logs car-log-gradio 2>&1 | grep -oP '\\[\\K[a-f0-9]{32}(?=\\])' | head -1)"
    exit 1
fi

echo "=========================================="
echo "Correlating logs for trace: $TRACE_ID"
echo "=========================================="
echo ""

# Check if containers are running
if ! docker ps --format '{{.Names}}' | grep -q "car-log"; then
    echo "Warning: No car-log containers found running"
    echo ""
fi

echo "=== MLflow Trace ==="
echo "Checking MLflow at $MLFLOW_URL..."
curl -s "$MLFLOW_URL/api/2.0/mlflow/traces?trace_id=$TRACE_ID" 2>/dev/null | head -100 || echo "MLflow not available or trace not found"
echo ""

echo "=== Gradio Container Logs ==="
if docker ps --format '{{.Names}}' | grep -q "car-log-gradio"; then
    docker logs car-log-gradio 2>&1 | grep -i "$TRACE_ID" || echo "No matching logs found in Gradio container"
else
    echo "Gradio container not running"
fi
echo ""

echo "=== Geo-routing Container Logs ==="
if docker ps --format '{{.Names}}' | grep -q "car-log-geo-routing"; then
    docker logs car-log-geo-routing 2>&1 | grep -i "$TRACE_ID" || echo "No matching logs found in geo-routing container"
else
    echo "Geo-routing container not running"
fi
echo ""

echo "=== MLflow Container Logs ==="
if docker ps --format '{{.Names}}' | grep -q "car-log-mlflow"; then
    docker logs car-log-mlflow 2>&1 | grep -i "$TRACE_ID" || echo "No matching logs found in MLflow container"
else
    echo "MLflow container not running"
fi
echo ""

echo "=========================================="
echo "Correlation complete for: $TRACE_ID"
echo "=========================================="
