#!/bin/bash

# Weather Data Backend Deployment Script for Google Cloud Run

# Set variables (replace with your actual values)
PROJECT_ID="master-shell-460708-e0"
SERVICE_NAME="weather-data-backend"
REGION="us-central1"
BUCKET_NAME="weather-data-bucket-$(date +%s)" # Unique bucket name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of Weather Data Backend...${NC}"

# Check if required tools are installed
command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}gcloud CLI is required but not installed. Aborting.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed. Aborting.${NC}" >&2; exit 1; }

# Step 1: Configure gcloud project
echo -e "${YELLOW}Step 1: Setting up Google Cloud project...${NC}"
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo -e "${YELLOW}Step 2: Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com

# Step 3: Create GCS bucket
echo -e "${YELLOW}Step 3: Creating Google Cloud Storage bucket...${NC}"
gsutil mb gs://$BUCKET_NAME || echo "Bucket might already exist, continuing..."

# Step 4: Build and deploy to Cloud Run
echo -e "${YELLOW}Step 4: Building and deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars GCS_BUCKET_NAME=$BUCKET_NAME \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300

# Step 5: Get service URL
echo -e "${YELLOW}Step 5: Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}Bucket Name: $BUCKET_NAME${NC}"

# Test the health endpoint
echo -e "${YELLOW}Testing health endpoint...${NC}"
curl -s "$SERVICE_URL/health" | python3 -m json.tool

echo -e "${GREEN}Deployment script completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test your API endpoints using the service URL above"
echo "2. Update your documentation with the actual service URL"
echo "3. Configure any additional monitoring or logging as needed"