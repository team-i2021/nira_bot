global steam_server_list, ex_reaction_list, reaction_bool_list, welcome_id_list, srtr_bool_list, all_reaction_list, bump_list, notify_token, role_keeper, restore_save, force_ss_list, mod_list, mc_server_list, welcome_message_list, autorole, pinMessage

steam_server_list = {}
ex_reaction_list = {}
reaction_bool_list = {}
welcome_id_list = {}
srtr_bool_list = {}
all_reaction_list = {}
bump_list = {}
notify_token = {}
role_keeper = {}
force_ss_list = {}
# {guild_id:[channel_id, message_id]}
mod_list = {}
# {guild_id:{"counter":100, "role":568902157372910}}
mc_server_list = {}

welcome_message_list = {}

autorole = {}

pinMessage = {}

global pid_ss
pid_ss={}

on_ali = ["1", "on", "On", "ON", "true", "True", "TRUE", "yes", "Yes", "YES"]
off_ali = ["0", "off", "Off", "OFF", "false", "False", "FALSE", "no", "No", "NO"]

py_admin = []

# 変数とかのリスト
save_list = [
        "steam_server_list",
        "reaction_bool_list",
        "welcome_id_list",
        "ex_reaction_list",
        "srtr_bool_list",
        "all_reaction_list",
        "bump_list",
        "notify_token",
        "role_keeper",
        "force_ss_list",
        "mod_list",
        "mc_server_list",
        "welcome_message_list",
        "autorole",
        "pinMessage"
        ]