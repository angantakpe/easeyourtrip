# EaseYourTrip Document AI Makefile
# Provides convenient commands for managing the application

.PHONY: help start stop restart status logs clean build rebuild test frontend frontend-stop all-stop install-dev update-deps setup db-setup db-reset db-init-vector

# Default target
help:
	@echo "EaseYourTrip Document AI - Makefile Commands"
	@echo "----------------------------------------"
	@echo "make start         - Start all services (app, postgres, poppler, ollama)"
	@echo "make start-unified - Start all services with unified configuration"
	@echo "make start-optimized - Start all services with optimized build settings for Windows"
	@echo "make stop          - Stop all services"
	@echo "make restart       - Restart all services"
	@echo "make status        - Show status of all services"
	@echo "make logs          - Show logs from all services"
	@echo "make logs-app      - Show logs from the app service only"
	@echo "make clean         - Remove all containers, networks, and volumes"
	@echo "make build         - Build all Docker images"
	@echo "make rebuild       - Rebuild all Docker images (no cache)"
	@echo "make test          - Run tests"
	@echo "make frontend      - Start the Streamlit frontend"
	@echo "make frontend-stop - Stop the Streamlit frontend"
	@echo "make all-stop      - Stop all services including frontend"
	@echo "make install-dev   - Install development dependencies"
	@echo "make update-deps   - Update dependencies in requirements.txt"
	@echo "make setup         - Set up initial directories"
	@echo "make db-setup      - Set up PostgreSQL with pgvector extension"
	@echo "make db-reset      - Reset PostgreSQL data (WARNING: deletes all data)"
	@echo "make db-init-vector - Initialize pgvector extension and create required tables"

# Start all services
start:
	@echo "Starting all services..."
	docker-compose up -d

# Start with unified configuration
start-unified:
	@echo "Starting all services with unified configuration..."
	docker-compose -f docker-compose.unified.yml up -d

# Start with optimized build settings for Windows
start-optimized:
	@echo "Starting all services with optimized build settings for Windows..."
	powershell -ExecutionPolicy Bypass -File docker-build-optimize.ps1

# Stop all services
stop:
	@echo "Stopping all services..."
	docker-compose down

# Restart all services
restart:
	@echo "Restarting all services..."
	docker-compose restart

# Show status of all services
status:
	@echo "Service status:"
	docker-compose ps

# Show logs from all services
logs:
	@echo "Showing logs from all services..."
	docker-compose logs

# Show logs from the app service only
logs-app:
	@echo "Showing logs from the app service..."
	docker-compose logs app

# Clean up all containers, networks, and volumes
clean:
	@echo "Cleaning up all containers, networks, and volumes..."
	docker-compose down -v
	docker system prune -f

# Build all Docker images
build:
	@echo "Building all Docker images..."
	docker-compose build

# Rebuild all Docker images (no cache)
rebuild:
	@echo "Rebuilding all Docker images (no cache)..."
	docker-compose build --no-cache

# Run tests
test:
	@echo "Running tests..."
	docker-compose run --rm app pytest

# Start the Streamlit frontend
frontend:
	@echo "Starting Streamlit frontend..."
	cd streamlit && docker-compose up -d

# Stop the Streamlit frontend
frontend-stop:
	@echo "Stopping Streamlit frontend..."
	cd streamlit && docker-compose down

# Stop all services including frontend
all-stop:
	@echo "Stopping all services including frontend..."
	cd streamlit && docker-compose down || true
	docker-compose down

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt

# Update dependencies in requirements.txt
update-deps:
	@echo "Updating dependencies in requirements.txt..."
	pip freeze > requirements.txt

# Poppler installation (legacy, now handled by Docker)
poppler:
	@echo "Installing Poppler for PDF processing"
	@echo "Note: Poppler is now handled by Docker, this command is kept for reference"

# Start FastAPI server
start-fastapi:
	@echo "Starting FastAPI server..."
	python -m uvicorn fast_api:app --reload --port 5321

# Stop FastAPI server
stop-fastapi:
	@echo "Stopping FastAPI server..."
	pkill -f "uvicorn fast_api:app --reload --port 5321"

# Restart FastAPI server
restart-fastapi:
	@echo "Restarting FastAPI server..."
	pkill -f "uvicorn fast_api:app --reload --port 5321" || true
	python -m uvicorn fast_api:app --reload --port 5321

# Show status of FastAPI server
status-fastapi:
	@echo "Status of FastAPI server:"
	pkill -f "uvicorn fast_api:app --reload --port 5321" || true
	python -m uvicorn fast_api:app --reload --port 5321

# Show logs from FastAPI server
logs-fastapi:
	@echo "Showing logs from FastAPI server..."
	python -m uvicorn fast_api:app --reload --port 5321

# Clean up FastAPI server
clean-fastapi:
	@echo "Cleaning up FastAPI server..."
	pkill -f "uvicorn fast_api:app --reload --port 5321"

# Start Streamlit frontend
start-streamlit:
	@echo "Starting Streamlit frontend..."
	cd streamlit && python -m streamlit run app.py

setup-streamlit:
	@echo "Setting up Streamlit frontend..."
	cd streamlit && uv pip install -r requirements.txt

setup:
	@echo "Setting up environment..."
	mkdir -p logs && mkdir -p static && mkdir -p init-scripts

# # Database setup commands
# db-setup: setup
# 	@echo "Setting up PostgreSQL with pgvector extension..."
# 	@echo "Creating init-scripts directory..."
# 	mkdir -p init-scripts
# 	@echo "Creating pgvector initialization script..."
# 	cat > init-scripts/01-init-pgvector.sql << 'EOF'
# -- Install the pgvector extension
# CREATE EXTENSION IF NOT EXISTS vector;

# -- Create the image_embedding_clip table with vector support
# CREATE TABLE IF NOT EXISTS public.image_embedding_clip (
#     id SERIAL PRIMARY KEY,
#     category VARCHAR(255) NOT NULL,
#     embeddings VECTOR(512), -- CLIP embeddings are typically 512-dimensional vectors
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     image_path VARCHAR(255),
#     description TEXT
# );

# -- Create an index for similarity search
# CREATE INDEX IF NOT EXISTS idx_image_embedding_clip_embeddings ON public.image_embedding_clip USING ivfflat (embeddings vector_cosine_ops);

# -- Add permissions
# GRANT ALL PRIVILEGES ON TABLE public.image_embedding_clip TO easeyourtrip;
# GRANT USAGE, SELECT ON SEQUENCE image_embedding_clip_id_seq TO easeyourtrip;
# EOF
# 	@echo "Updating docker-compose.yml to use pgvector image..."
# 	powershell -Command "(Get-Content docker-compose.yml) -replace 'image: postgres:16', 'image: pgvector/pgvector:pg16' | Set-Content docker-compose.yml"
# 	powershell -Command "if (-not (Select-String -Path docker-compose.yml -Pattern './init-scripts:/docker-entrypoint-initdb.d')) { (Get-Content docker-compose.yml) -replace '- postgres-data:/var/lib/postgresql/data', '- postgres-data:/var/lib/postgresql/data\n      - ./init-scripts:/docker-entrypoint-initdb.d' | Set-Content docker-compose.yml }"
# 	@echo "Stopping existing containers..."
# 	docker-compose down
# 	@echo "Starting containers with pgvector..."
# 	docker-compose up -d

# Reset PostgreSQL data (WARNING: deletes all data)
db-reset:
	@echo "WARNING: This will delete all PostgreSQL data. Press Ctrl+C to cancel or any key to continue..."
	@timeout 5
	@echo "Stopping containers..."
	docker-compose down
	@echo "Removing PostgreSQL volume..."
	docker volume rm document-ai_postgres-data || true
	@echo "Starting containers..."
	docker-compose up -d

# Initialize pgvector extension and create required tables
db-init-vector:
	@echo "Initializing pgvector extension and creating required tables..."
	@echo "Waiting for PostgreSQL to be ready..."
	@timeout 5
	docker exec -it document-ai-postgres-1 psql -U easeyourtrip -d easeyourtrip -c "CREATE EXTENSION IF NOT EXISTS vector;"
	docker exec -it document-ai-postgres-1 psql -U easeyourtrip -d easeyourtrip -f /docker-entrypoint-initdb.d/01-init-pgvector.sql
	@echo "Vector extension and tables initialized successfully!"