.PHONY: build run push docker-build k8s-apply clean

# Local Docker Compose
run:
	docker-compose up --build

# Build image only
docker-build:
	docker build -t publication-assistant:latest .

# Push to registry (replace with your repo)
push:
	docker tag publication-assistant:latest your-registry/publication-assistant:latest
	docker push your-registry/publication-assistant:latest

# Kubernetes
k8s-apply:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	# Apply secrets after editing secrets.yaml
	# kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/ingress.yaml

k8s-delete:
	kubectl delete -f k8s/ingress.yaml
	kubectl delete -f k8s/service.yaml
	kubectl delete -f k8s/deployment.yaml
	kubectl delete -f k8s/configmap.yaml
	kubectl delete -f k8s/namespace.yaml

clean:
	docker-compose down --volumes --remove-orphans
	docker system prune -f
