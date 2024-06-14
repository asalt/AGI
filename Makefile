.PHONY: setup clean test

setup:
	@echo "Setting up virtual environment and installing dependencies..."
	./setup.sh

test:
	@echo "Running unit tests..."
	./run_tests.sh

clean:
	@echo "Cleaning up..."
	rm -rf __pycache__
	rm -rf .Rhistory

