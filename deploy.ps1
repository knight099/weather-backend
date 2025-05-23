# Weather Data Backend Deployment Script for Google Cloud Run (PowerShell)

# Set variables (replace with your actual values)
$PROJECT_ID = "master-shell-460708-e0"
$SERVICE_NAME = "weather-data-backend"
$REGION = "asia-south2"
$BUCKET_NAME = "weather-data-bucket-$(Get-Date -Format 'yyyyMMddHHmmss')" # Unique bucket name

Write-Host "Starting deployment of Weather Data Backend..." -ForegroundColor Green

# Check if required tools are installed
try {
    gcloud --version | Out-Null
} catch {
    Write-Host "gcloud CLI is required but not installed. Aborting." -ForegroundColor Red
    exit 1
}

try {
    docker --version | Out-Null
} catch {
    Write-Host "Docker is required but not installed. Aborting." -ForegroundColor Red
    exit 1
}

# Step 1: Configure gcloud project
Write-Host "Step 1: Setting up Google Cloud project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
Write-Host "Step 2: Enabling required Google Cloud APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com

# Step 3: Create GCS bucket
Write-Host "Step 3: Creating Google Cloud Storage bucket..." -ForegroundColor Yellow
try {
    gsutil mb gs://$BUCKET_NAME
} catch {
    Write-Host "Bucket might already exist, continuing..."
}

# Step 4: Build and deploy to Cloud Run
Write-Host "Step 4: Building and deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --source . `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars GCS_BUCKET_NAME=$BUCKET_NAME `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --timeout 300

# Step 5: Get service URL
Write-Host "Step 5: Getting service URL..." -ForegroundColor Yellow
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
Write-Host "Bucket Name: $BUCKET_NAME" -ForegroundColor Green

# Test the health endpoint
Write-Host "Testing health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$SERVICE_URL/health" -Method Get
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Could not test health endpoint: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Deployment script completed!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test your API endpoints using the service URL above"
Write-Host "2. Update your documentation with the actual service URL"
Write-Host "3. Configure any additional monitoring or logging as needed" 