deploy:
	APP_VERSION=$(shell git describe --tags --always) docker compose up -d --build
