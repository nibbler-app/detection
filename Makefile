.PHONY: help bump bundle serve tag release

# Default target
help:
	@echo "Detection Engine - Available Commands"
	@echo ""
	@echo "Version Management:"
	@echo "  make bump          Bump version (interactive)"
	@echo "  make tag           Create and push git tag for current VERSION"
	@echo ""
	@echo "Building:"
	@echo "  make bundle        Create distribution bundle (tar.gz)"
	@echo ""
	@echo "Development:"
	@echo "  make serve         Start distribution server on port 8082"
	@echo ""

# Version bumping
bump:
	@./scripts/bump.sh

# Building
bundle:
	@./scripts/bundle.sh

# Development server
serve:
	@if [ ! -d "venv" ]; then \
		echo "Error: venv not found"; \
		exit 1; \
	fi
	@./venv/bin/python scripts/serve.py

# Git tagging
tag:
	@VERSION=$$(cat VERSION); \
	echo "Creating tag v$$VERSION..."; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	echo "Pushing tag v$$VERSION..."; \
	git push origin "v$$VERSION"; \
	echo "Tag v$$VERSION created and pushed successfully!"
