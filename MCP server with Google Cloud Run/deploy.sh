#!/bin/bash
OPENWEATHERMAP_API_KEY='your-openweathermap-api-key'
PROJECT_ID='your-project-id'
REGION='project-region'
# Weather Intelligence MCP Server - Google Cloud Run Deployment Script
# This script automates the deployment process

set -e  # Exit on any error

echo "🌤️ Weather Intelligence MCP Server - Google Cloud Run Deployment"
echo "=================================================================="

# Check if required tools are installed
command -v gcloud >/dev/null 2>&1 || { echo "❌ gcloud CLI is required but not installed. Aborting." >&2; exit 1; }

# Get project ID
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo "❌ PROJECT_ID not set and no default project configured."
        echo "   Set PROJECT_ID environment variable or run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
fi

echo "📋 Using Project ID: $PROJECT_ID"

# Get API key
if [ -z "$OPENWEATHERMAP_API_KEY" ]; then
    echo "❌ OPENWEATHERMAP_API_KEY environment variable is required."
    echo "   Get your API key from: https://openweathermap.org/api"
    echo "   Then run: export OPENWEATHERMAP_API_KEY=your_api_key_here"
    exit 1
fi

echo "🔑 OpenWeatherMap API key configured"

# Step 1: Create Artifact Registry repository (if it doesn't exist)
echo ""
echo "📦 Step 1: Setting up Artifact Registry repository..."
if gcloud artifacts repositories describe remote-mcp-servers --location=$REGION >/dev/null 2>&1; then
    echo "   ✅ Repository 'remote-mcp-servers' already exists"
else
    echo "   🔨 Creating Artifact Registry repository..."
    gcloud artifacts repositories create remote-mcp-servers \
        --repository-format=docker \
        --location=$REGION \
        --description="Repository for remote MCP servers" \
        --project=$PROJECT_ID
    echo "   ✅ Repository created successfully"
fi

# Step 2: Build and push container
echo ""
echo "🏗️  Step 2: Building and pushing container image..."
gcloud builds submit --region=$REGION--tag $REGION-docker.pkg.dev/$PROJECT_ID/remote-mcp-servers/weather-mcp-server:latest

# Step 3: Deploy to Cloud Run
echo ""
echo "🚀 Step 3: Deploying to Cloud Run..."
gcloud run deploy weather-mcp-server \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/remote-mcp-servers/weather-mcp-server:latest \
    --region=$REGION \
    --set-env-vars OPENWEATHERMAP_API_KEY=$OPENWEATHERMAP_API_KEY

# Step 4: Make service publicly accessible
echo ""
echo "🌐 Step 4: Making service publicly accessible..."
gcloud run services add-iam-policy-binding weather-mcp-server \
    --region=$REGION \
    --member="allUsers" \
    --role="roles/run.invoker"

# Get service URL
SERVICE_URL=$(gcloud run services describe weather-mcp-server --region=$REGION --format='value(status.url)')

echo ""
echo "🎉 Deployment completed successfully!"
echo "=================================================================="
echo "📍 Service URL: $SERVICE_URL"
echo "🔗 MCP Endpoint: $SERVICE_URL/mcp/"
echo ""
echo "🧪 To test your deployment:"
echo "   python simple_test.py"
echo ""
echo "🛠️  Available MCP Tools:"
echo "   • get_current_weather - Get current weather for any location"
echo "   • get_weather_forecast - Get multi-day weather forecast"
echo ""
echo "✅ Your Weather Intelligence MCP Server is ready!"