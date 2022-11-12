coverage run --parallel-mode -m unittest discover --start-directory tests --pattern "test_*.py"
coverage combine
coverage report --show-missing
coverage html