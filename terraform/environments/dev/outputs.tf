output "documents_bucket_name" {
  description = "Name of the document storage bucket (set as GCS_BUCKET_NAME in backend env)."
  value       = module.documents_bucket.name
}

output "documents_bucket_url" {
  description = "gs:// URL of the document storage bucket."
  value       = module.documents_bucket.url
}
