.PHONY: dev serve sam-local clean help

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Full stack local: nginx + mock API (Docker Compose)
	docker compose up --build

serve: ## Frontend only, no backend (instant, no Docker needed)
	npx serve frontend/ -l 3000

sam-local: ## Real Lambda via AWS SAM (requires Docker + CDK synth)
	cd cdk && cdk synth --no-staging > ../template.yaml
	@echo "Starting SAM on :3001 and frontend on :3000 ..."
	sam local start-api --template template.yaml --port 3001 &
	npx serve frontend/ -l 3000

clean: ## Stop containers and remove build artifacts
	docker compose down --volumes --remove-orphans
	rm -f template.yaml
