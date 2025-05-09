from utils import utils
from pyvaloapi.classes.User import User, Account, Pw
# from pyvaloapi.classes.mmr import CompetitiveUpdate, SeasonalInfo, QueueSkill, MMR, MMRParser, RankFetcher
import time
import flet as ft
import numpy as np
import requests as req
from datetime import datetime, timezone
from pyvaloapi.classes.Gui import Gui
import pyperclip as ppp
import urllib3
import json
import math

def main():
    api = utils()
    ui = Gui()
    print("すたと")
    user = api.user

    username = api.get_username()
    print(f"Username: {username}")

    print(f"Account Created At: {user.acct.created_at}")
    print(f"Country: {user.country}")
    print(f"Country at: {user.country_at}")
    # mmr = api.api.get_player_mmr(api.api.get_current_player_puuid())
    active_season = api.get_active_season()
    
    print(f"Active season: {active_season[0]['uuid']} / {active_season[0]['displayName']}")
    previous_season = api.get_previous_season()
    print(f"Previous season: {previous_season['uuid']} / {previous_season['displayName']}")

    # weapons = req.get("https://valorant-api.com/v1/weapons").json()["data"] # めっちゃ容量大きい 注意
    # vandal_id = "9c82e19d-4575-0200-1a81-3eacf00cf872"
    # vandal_data = api.find_obj(lambda x: x["uuid"] == vandal_id, weapons)[0]
    # loadout = api.api.get_current_match_loadout(api.api.get_current_match_id())["Guns"]
    # player_vandal = api.find_obj(lambda x: x["ID"] == vandal_id, loadout)[0]["SkinID"]
    # skin_info = api.find_obj(lambda x: x["uuid"] == player_vandal, vandal_data["skins"])[0]
    # print(skin_info)

    # GUI表示
    ft.app(target=lambda page: ui.main(page))
# try:
main()
# except Exception as e:
#     print(e)
input()