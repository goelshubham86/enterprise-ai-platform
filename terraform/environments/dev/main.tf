terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
  backend "gcs" {
    bucket = "enterprise-ai-tfstate-dev"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Modules ──────────────────────────────────────────────────
# Uncomment as each module is implemented

# module "networking" {
#   source     = "../../modules/networking"
#   project_id = var.project_id
#   region     = var.region
#   env        = "dev"
# }

# module "cloud_storage" {
#   source     = "../../modules/cloud-storage"
#   project_id = var.project_id
#   env        = "dev"
# }

# module "cloud_run_backend" {
#   source     = "../../modules/cloud-run"
#   project_id = var.project_id
#   region     = var.region
#   service    = "enterprise-ai-backend"
#   image      = var.backend_image
#   env        = "dev"
# }
