#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

# Exit on error
set -e

# --- Configuration ---
# GCP Project ID
PROJECT_ID='your-project-id'
# GCP Region
REGION='region'
# Name of the Artifact Registry repository
REPO_NAME='repo-name'
# Name of the Cloud Run service
SERVICE_NAME='service-name'

# --- Script ---

echo "--- Setting up Artifact Registry ---"
gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION --description="Weather agent repository" 2>/dev/null || echo "Repository already exists."

echo "--- Installing uv ---"
python -m pip install uv

echo "--- Generating uv.lock file ---"
uv lock

echo "--- Configuring Docker ---"
gcloud auth configure-docker $REGION-docker.pkg.dev

echo "--- Building the container image ---"
docker build --platform linux/amd64 -f Containerfile -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest .

echo "--- Pushing the image to Artifact Registry ---"
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest

echo "--- Deploying to Cloud Run ---"
gcloud run deploy $SERVICE_NAME \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --env-vars-file weather-agent.yaml

echo "--- Deployment complete ---"

