============================= test session starts ==============================
platform darwin -- Python 3.13.1, pytest-9.0.1, pluggy-1.6.0 -- /Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli
configfile: pyproject.toml
plugins: anyio-4.12.0, cov-7.0.0
collecting ... collected 7 items

tests/integration/test_docker_redis_f062.py::test_docker_compose_has_redis_service PASSED [ 14%]
tests/integration/test_docker_redis_f062.py::test_redis_uses_version_7 PASSED [ 28%]
tests/integration/test_docker_redis_f062.py::test_redis_has_persistence PASSED [ 42%]
tests/integration/test_docker_redis_f062.py::test_redis_has_volume PASSED [ 57%]
tests/integration/test_docker_redis_f062.py::test_redis_exposes_port_6379 PASSED [ 71%]
tests/integration/test_docker_redis_f062.py::test_redis_volume_persistence PASSED [ 85%]
tests/integration/test_docker_redis_f062.py::test_redis_command_configuration PASSED [100%]

============================== 7 passed in 0.07s ===============================
