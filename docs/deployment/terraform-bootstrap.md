# Terraform Bootstrap Guide

Before running `terraform init` for the first time, create the GCS state bucket
and grant the Cloud Build service account the necessary roles.

## 1. One-time state bucket creation

```bash
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1

# Create the Terraform remote state bucket
gcloud storage buckets create gs://enterprise-ai-tfstate-dev \
  --project=$PROJECT_ID \
  --location=$REGION \
  --uniform-bucket-level-access \
  --public-access-prevention

# Enable versioning so state file history is preserved
gcloud storage buckets update gs://enterprise-ai-tfstate-dev \
  --versioning
```

## 2. Grant Cloud Build SA the required roles

```bash
# Get the Cloud Build service account email
CB_SA="$(gcloud projects describe $PROJECT_ID \
  --format='value(projectNumber)')@cloudbuild.gserviceaccount.com"

# Terraform state bucket access
gcloud storage buckets add-iam-policy-binding gs://enterprise-ai-tfstate-dev \
  --member="serviceAccount:$CB_SA" \
  --role="roles/storage.admin"

# Manage GCS buckets in the project (documents bucket etc.)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/storage.admin"

# Push Docker images to Artifact Registry
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/artifactregistry.writer"

# Deploy to Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/run.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/iam.serviceAccountUser"
```

## 3. Create the Artifact Registry repository

```bash
gcloud artifacts repositories create enterprise-ai-platform \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID \
  --description="Enterprise AI Platform Docker images"
```

## 4. First local Terraform run

```bash
cd terraform/environments/dev

# Copy and fill in your tfvars
cp terraform.tfvars.example terraform.tfvars

terraform init
terraform validate
terraform plan
terraform apply
```

## 5. Triggering via Cloud Build

| Scenario | Command |
|---|---|
| PR — validate + plan only | Push branch → trigger fires with `_APPLY_INFRA=false` (default) |
| Deploy infra to dev | Set `_APPLY_INFRA=true` in the Cloud Build trigger substitutions |
| Deploy infra to prod | Use the `prod` trigger with `_ENV=prod _APPLY_INFRA=true` |
