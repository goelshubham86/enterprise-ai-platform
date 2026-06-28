# terraform/tests/

This directory is reserved for **Terratest** — Go-based infrastructure integration tests.

> **No Go code yet.** Terratest will be added after the core infrastructure modules
> (Cloud Run, Vertex AI, Networking) are complete. This placeholder ensures the
> directory structure is in place so the addition is a pure extension, not a
> structural change.

---

## What Terratest will do here

Terratest provisions real GCP resources in an isolated test project, runs
assertions against them, and tears everything down. Each test file maps to one
Terraform module.

### Planned test files

| File | Module under test | Key assertions |
|------|-------------------|---------------|
| `cloud_storage_test.go` | `modules/cloud-storage` | Bucket created, uniform access enforced, versioning on, public access blocked |
| `networking_test.go` | `modules/networking` | VPC + subnet created, serverless VPC connector healthy |
| `cloud_run_test.go` | `modules/cloud-run` | Service deployed, health endpoint returns 200, unauthenticated access blocked |
| `vertex_ai_test.go` | `modules/vertex-ai` | Index endpoint created, embedding dimension matches config |

---

## How Terratest fits into the CI pipeline

```
terraform/
├── modules/           ← units under test
├── environments/      ← integration compositions
├── tests/             ← this directory
│   ├── cloud_storage_test.go
│   ├── networking_test.go
│   ├── cloud_run_test.go
│   └── vertex_ai_test.go
└── .tflint.hcl

CI order:
  tf-fmt → tf-lint → tf-validate → tf-plan → [Terratest on PR merge to main]
```

Terratest is intentionally placed **after** `tf-plan` in CI — it provisions real
infrastructure and is slower (~5–15 min per module). It runs in a dedicated
`test` Cloud Build trigger against a `test` GCP project, not `dev`.

---

## Prerequisites (for when Terratest is added)

- Go 1.21+
- A dedicated `test` GCP project (never `dev`, never `prod`)
- Cloud Build SA granted `roles/editor` in the test project (scoped to CI only)
- `go.mod` + `go.sum` in this directory, listing `github.com/gruntwork-io/terratest`

---

## Running tests locally (future)

```bash
# From terraform/tests/
export GOOGLE_PROJECT=your-test-project-id
export GOOGLE_REGION=us-central1

go test -v -run TestCloudStorage -timeout 15m ./...
go test -v -run TestNetworking   -timeout 15m ./...
go test -v -timeout 30m ./...   # all tests
```
