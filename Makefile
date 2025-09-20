APP_NAME=myapp
IMAGE_NAME=$(APP_NAME):latest
DOCKERFILE=Dockerfile
PORT=8000



run:
	@echo "🚀 Starting FastAPI app locally..."
	@source ./venv/bin/activate

build:
	@echo "🐳 Building Docker image..."
	docker build -t $(IMAGE_NAME) -f $(DOCKERFILE) .

test:
	@echo "🧪 Running tests with pytest..."
	pytest tests/ --disable-warnings --maxfail=3

clean:
	@echo "🧹 Cleaning up __pycache__ and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -rf *.pyc *.pyo *.egg-info

push:
	@echo "📦 Pushing image to registry..."
	docker tag $(IMAGE_NAME) your-registry/$(IMAGE_NAME)
	docker push your-registry/$(IMAGE_NAME)
