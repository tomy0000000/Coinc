define USAGE
💰💱 Alfred Workflow for currencies conversion

Commands:
	install      Install dependencies for local development
	test         Run coverage unit tests

endef

export USAGE

help:
	@echo "$$USAGE"

install:
	flit install --deps develop --symlink

test:
	pytest --cov=coinc --cov-report=html --cov-report=xml
