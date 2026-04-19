# team/handlers.py - Simple wrapper

from .create_team import team_mode_start, register_create_team
from .join_team import register_join_team
from .match import register_match

def register_team_handlers(app):
    register_create_team(app)
    register_join_team(app)
    register_match(app)
