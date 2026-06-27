output "name" {
  description = "The globally unique name of the bucket."
  value       = google_storage_bucket.this.name
}

output "url" {
  description = "The gs:// URL of the bucket (use in application config)."
  value       = google_storage_bucket.this.url
}

output "self_link" {
  description = "The full resource self-link of the bucket."
  value       = google_storage_bucket.this.self_link
}

output "id" {
  description = "Bucket ID (same as name for GCS)."
  value       = google_storage_bucket.this.id
}

output "location" {
  description = "The location in which the bucket was created."
  value       = google_storage_bucket.this.location
}
