.PHONY: help bump bundle

# Default target
help:
	@echo "Detection Engine - Available Commands"
	@echo ""
	@echo "Version Management:"
	@echo "  make bump          Bump version (interactive)"
	@echo ""
	@echo "Building:"
	@echo "  make bundle        Create distribution bundle (tar.gz)"
	@echo ""

# Version bumping
bump:
	@./scripts/bump.sh

# Building
bundle:
	@./scripts/bundle.sh
