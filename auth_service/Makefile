# Performance Testing Makefile

.PHONY: install-locust setup-tests smoke-test load-test spike-test stress-test report clean-results

# Install locust and dependencies
install-locust:
	pip install locust faker
	echo "Locust installed successfully"

# Setup test environment
setup-tests:
	mkdir -p load_tests/results/{reports,history}
	python load_tests/test_data/generate_test_data.py
	docker-compose -f docker-compose.locust.yml up -d prometheus grafana
	@echo "Test environment setup complete"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

# Run smoke test
smoke-test:
	locust -f load_tests/locustfiles/smoke_test.py --headless --users 10 --spawn-rate 5 --run-time 2m --host=http://localhost:8000

# Run load test (1000 concurrent users)
load-test:
	locust -f load_tests/locustfiles/auth_load_test.py --headless --users 1000 --spawn-rate 100 --run-time 10m --host=http://localhost:8000 --csv=load_tests/results/history/auth_load

# Run spike test
spike-test:
	locust -f load_tests/locustfiles/spike_test.py --headless --users 2000 --spawn-rate 500 --run-time 5m --host=http://localhost:8000 --csv=load_tests/results/history/spike

# Run stress test
stress-test:
	locust -f load_tests/locustfiles/stress_test.py --headless --users 3000 --spawn-rate 300 --run-time 15m --host=http://localhost:8000 --csv=load_tests/results/history/stress

# Run all tests sequentially
performance-suite: smoke-test load-test spike-test stress-test

# Run with web UI (for interactive testing)
run-web-ui:
	locust -f load_tests/locustfiles/auth_load_test.py --host=http://localhost:8000

# Run distributed tests
run-distributed:
	docker-compose -f docker-compose.locust.yml up --scale locust-worker=4

# Generate performance report
report:
	python load_tests/scripts/generate_report.py

# Clean test results
clean-results:
	rm -rf load_tests/results/*
	docker-compose -f docker-compose.locust.yml down -v

# Monitor resources during tests
monitor-resources:
	watch -n 2 'echo "=== CPU/Memory ===" && docker stats --no-stream && echo "=== Network ===" && docker ps --format "table {{.Names}}\t{{.Ports}}"'

# Quick health check
health-check:
	curl -f http://localhost:8000/ || echo "Service is not healthy"