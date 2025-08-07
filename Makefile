# LocalStack Demo Makefile
# Usage: make <target>

.PHONY: help start stop status logs clean install demo advanced api cf health

# Default target
help: ## Show this help message
	@echo "LocalStack Demo - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Docker operations
start: ## Start LocalStack services
	@echo "🚀 Starting LocalStack..."
	docker-compose up -d
	@echo "⏳ Waiting for LocalStack to be ready..."
	@sleep 5
	@make health

stop: ## Stop LocalStack services
	@echo "🛑 Stopping LocalStack..."
	docker-compose down

restart: ## Restart LocalStack services
	@make stop
	@make start

status: ## Show LocalStack container status
	@echo "📊 LocalStack Status:"
	docker-compose ps

logs: ## Show LocalStack logs
	@echo "📋 LocalStack Logs:"
	docker-compose logs -f

health: ## Check LocalStack health
	@echo "🏥 Checking LocalStack health..."
	@curl -s http://localhost:4566/_localstack/health | python3 -m json.tool || echo "LocalStack not responding"

# Setup and installation
install: ## Install Python dependencies
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt awscli-local

# Demo operations
demo: ## Run complete Python demo (recommended)
	@echo "🚀 Running complete LocalStack demo..."
	python3 demo.py

demo-bash: ## Run bash/CLI demo
	@echo "💻 Running bash demo..."
	chmod +x setup-demo.sh
	./setup-demo.sh

# Infrastructure as Code
cf-deploy: ## Deploy CloudFormation stack
	@echo "☁️ Deploying CloudFormation stack..."
	chmod +x deploy-cloudformation.sh
	./deploy-cloudformation.sh

cf-delete: ## Delete CloudFormation stack
	@echo "🗑️ Deleting CloudFormation stack..."
	aws cloudformation delete-stack \
		--endpoint-url http://localhost:4566 \
		--stack-name localstack-demo-stack
	@echo "Stack deletion initiated"

cf-status: ## Show CloudFormation stack status
	@echo "📋 CloudFormation Stack Status:"
	@aws cloudformation describe-stacks \
		--endpoint-url http://localhost:4566 \
		--stack-name localstack-demo-stack \
		--query 'Stacks[0].{StackName:StackName,StackStatus:StackStatus}' \
		--output table || echo "Stack not found"

# Dashboard and monitoring
dashboard: ## Start dashboard server
	@echo "📊 Starting dashboard server..."
	python3 server.py

dashboard-browser: ## Open dashboard in browser
	@echo "🌐 Opening dashboard..."
	open http://localhost:8000/dashboard.html

# Utilities
clean: ## Clean up LocalStack data and containers
	@echo "🧹 Cleaning up LocalStack..."
	docker-compose down -v
	docker system prune -f
	rm -rf ./volume/cache/*
	rm -rf ./volume/logs/*
	rm -rf ./volume/tmp/*

clean-all: ## Clean everything including images
	@make clean
	@echo "🧹 Removing LocalStack images..."
	docker rmi localstack/localstack || true

reset: ## Reset LocalStack (clean + start)
	@make clean
	@make start

# Development helpers
shell: ## Open shell in LocalStack container
	docker exec -it localstack-main /bin/bash

aws-config: ## Show AWS CLI configuration for LocalStack
	@echo "⚙️ AWS CLI Configuration for LocalStack:"
	@echo "export AWS_ACCESS_KEY_ID=test"
	@echo "export AWS_SECRET_ACCESS_KEY=test"
	@echo "export AWS_DEFAULT_REGION=us-east-1"
	@echo ""
	@echo "Use --endpoint-url=http://localhost:4566 with AWS CLI commands"

endpoints: ## Show all LocalStack endpoints
	@echo "🌐 LocalStack Endpoints:"
	@echo "Main API:      http://localhost:4566"
	@echo "Health Check:  http://localhost:4566/_localstack/health"
	@echo "Service Info:  http://localhost:4566/_localstack/info"
	@echo "Dashboard:     http://localhost:8000/dashboard.html (when server.py is running)"

# Test everything
test-all: ## Run all demos and tests
	@echo "🧪 Running all tests..."
	@make demo
	@echo ""
	@make demo-bash
	@echo ""
	@echo "🎉 All tests completed!"

# Quick setup
quick-start: ## Quick start: install deps, start LocalStack, run demo
	@echo "⚡ Quick Start Setup..."
	@make install
	@make start
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@make demo
	@make dashboard-browser
