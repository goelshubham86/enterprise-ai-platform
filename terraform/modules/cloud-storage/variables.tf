# ─── Required ─────────────────────────────────────────────────

variable "project_id" {
  description = "GCP project ID in which the bucket will be created."
  type        = string
}

variable "name" {
  description = <<-EOT
    Logical bucket name (suffix). The final bucket name is:
      {project_id}-{name}-{env}
    Must be lowercase letters, numbers, and hyphens only.
  EOT
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.name))
    error_message = "name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "env" {
  description = "Deployment environment (dev | staging | prod)."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod."
  }
}

# ─── Location & Storage Class ──────────────────────────────────

variable "location" {
  description = <<-EOT
    Bucket location. Use a multi-region (US, EU, ASIA) for high availability
    or a single region (us-central1) to keep data co-located with Cloud Run.
  EOT
  type        = string
  default     = "US-CENTRAL1"
}

variable "storage_class" {
  description = "Default storage class. STANDARD for active data; NEARLINE/COLDLINE for archives."
  type        = string
  default     = "STANDARD"

  validation {
    condition     = contains(["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"], var.storage_class)
    error_message = "storage_class must be one of: STANDARD, NEARLINE, COLDLINE, ARCHIVE."
  }
}

# ─── Data Protection ──────────────────────────────────────────

variable "versioning_enabled" {
  description = "Enable object versioning for point-in-time recovery."
  type        = bool
  default     = true
}

variable "soft_delete_retention_days" {
  description = "Soft-delete retention period in days (0 to disable). Min 7 days when enabled."
  type        = number
  default     = 7

  validation {
    condition     = var.soft_delete_retention_days == 0 || var.soft_delete_retention_days >= 7
    error_message = "soft_delete_retention_days must be 0 (disabled) or >= 7."
  }
}

variable "force_destroy" {
  description = <<-EOT
    Allow Terraform to destroy a non-empty bucket. Set true only in dev/sandbox.
    Never true in staging or prod.
  EOT
  type        = bool
  default     = false
}

# ─── Access Control ───────────────────────────────────────────

variable "uniform_bucket_level_access" {
  description = "Enforce uniform bucket-level access (disables legacy object-level ACLs). Recommended: true."
  type        = bool
  default     = true
}

variable "public_access_prevention" {
  description = "Prevent public access. Use 'enforced' for all enterprise buckets."
  type        = string
  default     = "enforced"

  validation {
    condition     = contains(["enforced", "inherited"], var.public_access_prevention)
    error_message = "public_access_prevention must be 'enforced' or 'inherited'."
  }
}

# ─── IAM ──────────────────────────────────────────────────────

variable "object_readers" {
  description = "List of IAM members granted roles/storage.objectViewer (e.g. serviceAccount:sa@proj.iam.gserviceaccount.com)."
  type        = list(string)
  default     = []
}

variable "object_creators" {
  description = "List of IAM members granted roles/storage.objectCreator."
  type        = list(string)
  default     = []
}

variable "object_admins" {
  description = "List of IAM members granted roles/storage.objectAdmin."
  type        = list(string)
  default     = []
}

# ─── Encryption ───────────────────────────────────────────────

variable "kms_key_name" {
  description = "Cloud KMS key name for CMEK encryption. Leave null to use Google-managed keys."
  type        = string
  default     = null
}

# ─── Lifecycle ────────────────────────────────────────────────

variable "lifecycle_rules" {
  description = <<-EOT
    List of lifecycle rules applied to objects in the bucket.
    Each rule has an 'action' (type, storage_class) and 'condition' (age, etc.).
    Defaults to a cost-optimised tiered storage policy.
  EOT
  type = list(object({
    action = object({
      type          = string
      storage_class = optional(string)
    })
    condition = object({
      age                   = optional(number)
      num_newer_versions    = optional(number)
      with_state            = optional(string)
      matches_storage_class = optional(list(string))
    })
  }))
  default = [
    # Move non-current versions to Nearline after 30 days
    {
      action    = { type = "SetStorageClass", storage_class = "NEARLINE" }
      condition = { age = null, num_newer_versions = 1, with_state = "ARCHIVED", matches_storage_class = ["STANDARD"] }
    },
    # Delete non-current versions after 90 days
    {
      action    = { type = "Delete" }
      condition = { age = null, num_newer_versions = 3, with_state = "ARCHIVED", matches_storage_class = null }
    },
  ]
}

# ─── CORS ─────────────────────────────────────────────────────

variable "cors_origins" {
  description = "Origins allowed for CORS requests. Add frontend URL for direct browser uploads."
  type        = list(string)
  default     = []
}

variable "cors_methods" {
  description = "HTTP methods allowed for CORS."
  type        = list(string)
  default     = ["GET", "HEAD", "PUT", "POST", "DELETE"]
}

variable "cors_max_age_seconds" {
  description = "CORS preflight cache duration in seconds."
  type        = number
  default     = 3600
}

# ─── Logging ──────────────────────────────────────────────────

variable "log_bucket_name" {
  description = "Destination bucket for access logs. Leave null to disable logging."
  type        = string
  default     = null
}

variable "log_object_prefix" {
  description = "Prefix for log objects written to the log bucket."
  type        = string
  default     = "storage-access-logs/"
}

# ─── Labels ───────────────────────────────────────────────────

variable "labels" {
  description = "Additional labels to merge with the standard label set."
  type        = map(string)
  default     = {}
}
