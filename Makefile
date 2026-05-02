make run_discord:
	uv run python3 src/steamjoin_discbot/__main__.py --config CONFIG

make run_server_dev:
	uv run fastapi dev src/steamjoin_server/__init__.py

make run_server:
	uv run fastapi run src/steamjoin_server/__init__.py