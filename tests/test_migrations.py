import unittest

from alembic.config import Config
from alembic.script import ScriptDirectory


class TestMigrations(unittest.TestCase):
    def test_only_single_head_revision_in_migrations(self):
        config = Config()
        config.set_main_option("script_location", "migrations")
        script = ScriptDirectory.from_config(config)

        # This will raise if there are multiple heads
        script.get_current_head()
