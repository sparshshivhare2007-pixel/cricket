from .user_info import register_user_info
from .user_ranks import register_user_ranks
from .member_lists import register_member_lists
from .startgame import register_startgame
from .matches import register_matches
from .help import register_help
from .live_matches import register_live_matches
# from .batting import register_batting  # Team mode - comment out
# from .bowling import register_bowling  # Team mode - comment out
from .host_change import register_host_change
from .solo_leave import register_solo_leave
from .full_score import register_full_score
from .report_user import register_report_user
from .report_stats import register_report_stats
# from .cap_change import register_cap_change  # Team mode - comment out
# from .add_cap import register_add_cap  # Team mode - comment out
# from .rm_cap import register_rm_cap  # Team mode - comment out

def register_extra_commands(app):
    register_user_info(app)
    register_user_ranks(app)
    register_member_lists(app)
    register_startgame(app)
    register_matches(app)
    register_help(app)
    register_live_matches(app)
    # register_batting(app)  # Team mode - comment out
    # register_bowling(app)  # Team mode - comment out
    register_host_change(app)
    register_solo_leave(app)
    register_full_score(app)
    register_report_user(app)
    register_report_stats(app)
    # register_cap_change(app)  # Team mode - comment out
    # register_add_cap(app)  # Team mode - comment out
    # register_rm_cap(app)  # Team mode - comment out