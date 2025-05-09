import flet as ft

import json
from utils import utils
from pyvaloapi.classes.User import User, Account, Pw
import time
import asyncio
import threading
import requests
import math
import os
import re
import traceback


class Gui:
    def main(self, page: ft.Page):
        self.util = utils()
        self.view_name = None
        self.page = page
        self.has_got_liveview = False
        self.loadout_cache = None
        self.lastMatchID = None
        self.skins = {}
        self.game_info = None
        self.currentWeapon = "Vandal"
        self.game_state = self.util.api.get_game_state(self.util.api.get_presence())
        page.title = f"Welcome {self.api.get_username()} | Valo tracker"
        page.window.height = 650
        page.window.width = 1100
        page.window.maximizable = False
        page.window.resizable = False

        self.weaponsMap = None

        self.liveview_Data = {}

        # Overview用変数
        self.overview = {
            # "unrated": { 例
            #     "name": "Unrated",
            #     "win": 0,
            #     "lose": 0,
            #     "head": 0,
            #     "body": 0,
            #     "legs": 0,
            #     "dmg_per_round": 0,
            #     "kd": 0,
            #     "kill": 0,
            #     "death": 0,
            #     "assist": 0,
            #     "clutch": 0,
            #     "total_damages": 0,
            #     "matches": 0
            # }
            "unrated": None,
            "competitive": None,
            "swiftplay": None,
            "deathmatch": None,
            "hurm": None,
        }

        self.games_map = {
            "Unrated": "unrated",
            "Swiftplay": "swiftplay",
            "Competitive": "competitive",
            "Deathmatch": "deathmatch",
            "Team Deathmatch": "hurm",
        }
        self.games = ["unrated", "competitive", "swiftplay", "deathmatch", "hurm"]

        self.total = 0  # ぷろぐれす
        self.current = 0  # ぷろぐれす

        def get_overview_data():  # ゲロメンドイ
            self.current = 0
            self.total = 0
            me_id = self.util.api.puuid
            matches = self.util.get_histories()

            for game in self.games:
                if matches is not None:
                    self.total += len(matches[game])

            for game in self.games:
                average_dmg = 0
                try:
                    headshot = 0
                    bodyshot = 0
                    legshot = 0
                    total_hit = 0

                    win = 0
                    lose = 0

                    for match in matches[game]:
                        if self.view_name != "overview":
                            return
                        damages = 0
                        round_count = 0
                        detail = self.api.decrypt_history(match["id"])
                        if (detail) == None:
                            continue
                        queue_id = detail["matchInfo"]["queueID"]  # ゲームモードのid
                        players = detail["players"]
                        me = self.util.find_obj(
                            lambda x: x["subject"] == me_id, players
                        )[0]
                        me_team = me["teamId"]
                        teamIndex = 0 if me_team == "Red" else 1

                        team_result = detail["teams"][teamIndex]
                        won = team_result["won"]
                        if won == False:
                            lose += 1
                        else:
                            win += 1

                        stats = me["stats"]
                        roundsPlayed = stats["roundsPlayed"]

                        round_damages = me["roundDamage"] or []
                        round_count += roundsPlayed
                        for damage in round_damages:
                            damages += damage["damage"]

                        average_dmg += damages / roundsPlayed if roundsPlayed > 0 else 1

                        for _round in detail["roundResults"]:
                            p = _round["playerStats"]
                            ore = self.util.find_obj(
                                lambda x: x["subject"] == me_id, p
                            )[0]
                            damagesList = ore["damage"]
                            for damage in damagesList:
                                headshot += damage["headshots"]
                                total_hit += damage["headshots"]
                                bodyshot += damage["bodyshots"]
                                total_hit += damage["bodyshots"]
                                legshot += damage["legshots"]
                                total_hit += damage["legshots"]

                        h = self.overview.get(queue_id) or {}
                        h["lose"] = (h.get("lose") or 0) + lose
                        h["win"] = (h.get("win") or 0) + win
                        h["win_percentage"] = math.floor(win / (len(matches)) * 100)
                        h["kill"] = (h.get("kill") or 0) + stats["kills"]
                        h["death"] = (h.get("deaths") or 0) + stats["deaths"]
                        h["assist"] = (h.get("assists") or 0) + stats["assists"]
                        h["total_damages"] = (h.get("total_damages") or 0) + damages
                        h["dmg_per_round"] = round(average_dmg / len(matches[game]), 2)
                        h["matches"] = len(matches[game])
                        h["total_hit"] = (h.get("total_hit") or 0) + total_hit
                        h["headshot"] = (h.get("headshot") or 0) + headshot
                        h["bodyshot"] = (h.get("bodyshot") or 0) + bodyshot
                        h["legshot"] = (h.get("legshot") or 0) + legshot
                        h["hs"] = "N/A" if total_hit == 0 else math.floor((headshot / total_hit) * 100)
                        h["kd"] = "N/A" if stats["kills"] == 0 else round(stats["kills"] / (stats["deaths"] if stats["deaths"] > 0 else 1), 2)
                        self.overview[queue_id] = h

                        self.current += 1

                        if self.view_name == "overview":
                            page.controls.clear()
                            page.controls.append(
                                ft.Column(
                                    [
                                        ft.Container(
                                            content=ft.Column(
                                                [
                                                    ft.Text(
                                                        "Fetching data...", size=30
                                                    ),
                                                    ft.Text(
                                                        f"{str(self.current)}/{str(self.total)} ready",
                                                        size=20,
                                                        text_align=ft.TextAlign.CENTER,
                                                    ),
                                                ],
                                                alignment=ft.MainAxisAlignment.CENTER,
                                            ),
                                            alignment=ft.alignment.center,
                                            expand=True,
                                        ),
                                        ft.Divider(),
                                        footer,
                                    ],
                                    expand=True,
                                )
                            )
                            page.update()
                except Exception as e:
                    traceback.print_exc()
                    page.controls.clear()
                    page.controls.append(
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(e, size=30),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            alignment=ft.alignment.center,
                            expand=True,
                        )
                    )
                    page.update()
                    pass
            page.controls.clear()

        # end

        # ページの中身（動的に切り替える用）
        content_area = ft.Column()

        def update_clicked():
            updateOverView()

        def get_combat_info(gamename):
            data = self.overview[gamename]
            if data == None:
                return ft.Column(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        f"No data found",
                                        weight=ft.FontWeight.BOLD,
                                        size=25.5,
                                    )
                                ]
                            ),
                            margin=ft.margin.only(left=10, right=10, top=10, bottom=5),
                        )
                    ]
                )
            return ft.Column(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"Last {data['matches']} matches",
                                    weight=ft.FontWeight.BOLD,
                                    size=25.5,
                                ),
                                ft.Divider(),
                                ft.Row(
                                    [
                                        ft.Text(f"Kills:", size=18.5),
                                        ft.Text(
                                            f"{data['kill']}",
                                            weight=ft.FontWeight.BOLD,
                                            size=20.5,
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"Deaths:", size=18.5),
                                        ft.Text(
                                            f"{data['death']}",
                                            weight=ft.FontWeight.BOLD,
                                            size=20.5,
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"ADR:", size=18.5),
                                        ft.Text(
                                            f"{data['dmg_per_round']}",
                                            weight=ft.FontWeight.BOLD,
                                            size=20.5,
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"DMG / Match:", size=18.5),
                                        ft.Text(
                                            f"{round(data['total_damages'] / data['matches'], 2)}",
                                            weight=ft.FontWeight.BOLD,
                                            size=20.5,
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"HS%:", size=18.5),
                                        ft.Text(
                                            f"{data['hs']}%",
                                            weight=ft.FontWeight.BOLD,
                                            size=20.5,
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"KD:", size=18.5),
                                        ft.Text(
                                            f"{data['kd']}",
                                            weight=ft.FontWeight.BOLD,
                                            size=20.5,
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"Win%:", size=18.5),
                                        ft.Text(
                                            f"{data['win_percentage']}",
                                            weight=ft.FontWeight.BOLD,
                                            size=20.5,
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        margin=ft.margin.only(left=10, right=10, top=10, bottom=5),
                    )
                ]
            )

        # OverViewのguiをリクエスト
        def overviewGui():
            return ft.Column(
                [
                    # main title
                    ft.Column(
                        [
                            ft.Stack(
                                width=page.width,
                                height=65,
                                controls=[
                                    ft.Container(
                                        border_radius=10,
                                        bgcolor="#181c22",
                                        height=65,
                                    ),
                                    ft.Row(
                                        [
                                            ft.IconButton(
                                                ft.Icons.UPDATE,
                                                icon_size=30,
                                                icon_color=ft.colors.WHITE,
                                                on_click=lambda _: update_clicked(),
                                            ),
                                        ],
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        height=65,
                                    ),
                                ],
                            ),
                            ft.Divider(),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    drop,
                                    ft.Stack(
                                        controls=[
                                            ft.Container(  # combat info
                                                content=get_combat_info(
                                                    self.games_map[drop.value]
                                                ),
                                                border_radius=10,
                                                bgcolor="#181c22",
                                                width=box_width,
                                                height=box_height - 50,
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            ft.Container(  # nanika
                                border_radius=10,
                                bgcolor="#181c22",
                                width=box_width,
                                height=box_height,
                            ),
                            ft.Container(  # nanika 2
                                border_radius=10,
                                bgcolor="#181c22",
                                width=box_width,
                                height=box_height,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    ),
                    #
                ]
            )

        # 下のボタン関連の関数
        def updateFooter():
            footer.controls.clear()
            footer.controls.extend(
                [
                    ft.Column(
                        [
                            ft.TextButton(
                                content=ft.Text("Over View"),
                                on_click=lambda _: switch_view("overview"),
                            ),
                            ft.Container(
                                height=1,
                                width=90,
                                bgcolor=(
                                    ft.colors.BLUE
                                    if self.view_name == "overview"
                                    else ft.colors.TRANSPARENT
                                ),
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Text(" | "),  # 区切り
                    ft.Column(
                        [
                            ft.TextButton(
                                content=ft.Text("Live View"),
                                on_click=lambda _: switch_view("liveview"),
                            ),
                            ft.Container(
                                height=1,
                                width=90,
                                bgcolor=(
                                    ft.colors.BLUE
                                    if self.view_name == "liveview"
                                    else ft.colors.TRANSPARENT
                                ),
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Text(" | "),  # 区切り
                    ft.Column(
                        [
                            ft.TextButton(
                                content=ft.Text("Match History"),
                                on_click=lambda _: switch_view("matchhistory"),
                            ),
                            ft.Container(
                                height=1,
                                width=90,
                                bgcolor=(
                                    ft.colors.BLUE
                                    if self.view_name == "matchhistory"
                                    else ft.colors.TRANSPARENT
                                ),
                            ),
                        ],
                        spacing=2,
                    ),
                ]
            )

        # らいぶびゅーのGUI
        def get_liveview_data_ingame():
            while True:
                try:
                    gameID = self.util.api.get_current_match_id()
                    break
                except:
                    pass
                time.sleep(2)
            if gameID != None:
                self.liveview_Data.update({"id": gameID})
                game = self.util.api.get_current_match_info(gameID)
                all_players = game["Players"]
                if 1 == 1:
                    me = self.api.find_obj(
                        lambda x: x["Subject"] == self.api.api.puuid, all_players
                    )[0]
                    current_team = me["TeamID"]
                    names = {
                        player["Subject"]: f"{player['GameName']}#{player['TagLine']}"
                        for player in self.util.api.get_user_names(
                            [p["Subject"] for p in all_players]
                        )
                    }

                    self.loadout_cache = self.api.api.get_current_match_loadout(gameID)
                    if self.weaponsMap == None:
                        self.weaponsMap = {
                            data["displayName"]: data["uuid"]
                            for data in requests.get(
                                "https://valorant-api.com/v1/weapons"
                            ).json()["data"]
                        }
                    weaponID = self.weaponsMap[self.currentWeapon]
                    for weapon in self.loadout_cache["Loadouts"]:
                        p_loadout = weapon["Loadout"]
                        pid = p_loadout["Subject"]
                        if len(pid) > 0:
                            skinID = p_loadout["Items"][weaponID]["Sockets"][
                                "bcef87d6-209b-46c6-8b19-fbe40bd95abc"
                            ]["Item"]["ID"]
                            self.skins.update(
                                {
                                    pid: {
                                        "chroma": p_loadout["Items"][weaponID][
                                            "Sockets"
                                        ]["3ad1b2b2-acdb-4524-852f-954a76ddae0a"][
                                            "Item"
                                        ][
                                            "ID"
                                        ],
                                        "id": skinID,
                                    }
                                }
                            )

                    player_count = len(all_players)
                    current_loaded = 0
                    self.liveview_Data["players"] = []
                    for player in all_players:
                        if self.game_state != "INGAME":
                            return None
                        teamID = player["TeamID"]
                        team_color = "#19e0a4" if teamID == current_team else "#c91e3e"
                        name = names[player["Subject"]]
                        agentID = player["CharacterID"]
                        res = requests.get(
                            f"https://valorant-api.com/v1/agents/{agentID}"
                        ).json()["data"]
                        agentName = res["displayName"]
                        agentIcon = res["displayIcon"]
                        mmr = None
                        while mmr is None:
                            mmr_res = self.api.api.get_player_mmr(player["Subject"])
                            if mmr_res.get("code") is None:
                                mmr = mmr_res
                                break
                            time.sleep(1)

                        nowseason = self.api.get_active_season()[0]
                        season = nowseason["uuid"]

                        rank_icon = "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/0/smallicon.png"
                        cur_season_rank = 0
                        cur_s = None
                        seasons = None
                        peak = 0
                        win = 0
                        head = 0
                        peak_season_info = self.api.api.get_competitive_season(
                            self.api.get_active_season()[0]["uuid"]
                        )
                        peak_name = (
                            re.search(
                                r"CompetitiveSeason_(.*?)_DataAsset",
                                peak_season_info["assetPath"],
                            )
                            .group(1)
                            .replace("_", " ")
                            .replace("-1", "")
                            .replace("EpisodeV", "V")
                        )

                        rankList = requests.get(
                            "https://valorant-api.com/v1/competitivetiers"
                        ).json()["data"][-1]["tiers"]
                        if mmr.get("QueueSkills") is not None:
                            rankInfo = mmr["QueueSkills"]["competitive"][
                                "SeasonalInfoBySeasonID"
                            ]
                            if rankInfo is not None:
                                seasons = [{"id": k, **v} for k, v in rankInfo.items()]
                                seasons.sort(key=lambda x: x["Rank"], reverse=True)
                                peak = seasons[0]["Rank"]
                                peak_season_id = seasons[0]["id"]
                                peak_season_info = self.api.api.get_competitive_season(
                                    peak_season_id
                                )
                                peak_name = (
                                    re.search(
                                        r"CompetitiveSeason_(.*?)_DataAsset",
                                        peak_season_info["assetPath"],
                                    )
                                    .group(1)
                                    .replace("_", " ")
                                    .replace("-1", "")
                                    .replace("EpisodeV", "V")
                                )

                                cur_s = rankInfo.get(season)
                                if cur_s is not None:
                                    cur_season_rank = (
                                        cur_s["CompetitiveTier"]
                                        if cur_s is not None
                                        else 0
                                    )
                                    win = math.floor(
                                        (cur_s["NumberOfWins"] / cur_s["NumberOfGames"])
                                        * 100
                                    )
                        _history = self.api.api.get_match_history(
                            player["Subject"], "competitive", start=0, end=3
                        )
                        total_hit = 0
                        head_hit = 0
                        kills = 0
                        deaths = 1
                        kd = 0.00
                        if _history.get("History") is not None:
                            history = _history.get("History")

                            for h2 in history:
                                id = h2["MatchID"]
                                detail = self.api.api.get_match_details(id)
                                if detail.get("roundResults") is not None:
                                    info = detail["roundResults"]

                                    me_stats = self.api.find_obj(
                                        lambda x: x["subject"] == player["Subject"],
                                        detail["players"],
                                    )[0]["stats"]
                                    kills += me_stats["kills"]
                                    deaths += me_stats["deaths"]

                            for h in history[0:2]:
                                id = h["MatchID"]
                                detail = self.api.api.get_match_details(id)
                                if detail.get("roundResults") is not None:
                                    info = detail["roundResults"]

                                    me_stats = self.api.find_obj(
                                        lambda x: x["subject"] == player["Subject"],
                                        detail["players"],
                                    )[0]["stats"]
                                    kills += me_stats["kills"]
                                    deaths += me_stats["deaths"]

                                    for _round in info:
                                        p_stats = _round["playerStats"]
                                        me = self.api.find_obj(
                                            lambda x: x["subject"] == player["Subject"],
                                            p_stats,
                                        )[0]
                                        me_dmg = me["damage"]

                                        for dmg in me_dmg:
                                            total_hit += dmg["bodyshots"]
                                            total_hit += dmg["legshots"]
                                            total_hit += dmg["headshots"]
                                            head_hit += dmg["headshots"]
                        head = math.floor(
                            (head_hit / total_hit if total_hit > 0 else 1) * 100
                        )
                        kd = round(kills / deaths if deaths > 0 else 1, 2)

                        cur_rank = self.api.find_obj(
                            lambda x: x["tier"] == cur_season_rank, rankList
                        )[0]
                        peak_rank = self.api.find_obj(
                            lambda x: x["tier"] == peak, rankList
                        )[0]
                        rank_icon = cur_rank["smallIcon"]
                        peak_icon = peak_rank["smallIcon"]

                        weapons = requests.get(
                            f"https://valorant-api.com/v1/weapons"
                        ).json()
                        vandal_info = self.api.find_obj(
                            lambda x: x["uuid"] == weaponID, weapons["data"]
                        )[0]
                        skin = self.api.find_obj(
                            lambda x: x["uuid"] == self.skins[player["Subject"]]["id"],
                            vandal_info["skins"],
                        )[0]

                        objSkin = self.api.find_obj(
                            lambda x: x["uuid"]
                            == self.skins[player["Subject"]]["chroma"],
                            skin["chromas"],
                        )
                        if len(objSkin) > 0:
                            skin_info = objSkin[0]
                            skinName = skin_info["displayName"]
                            skinIcon = skin_info["fullRender"]
                        else:
                            skinName = "Vandal"
                            skinIcon = "https://media.valorant-api.com/weaponskinchromas/19629ae1-4996-ae98-7742-24a240d41f99/fullrender.png"

                        self.liveview_Data["players"].append(
                            {
                                "Subject": player["Subject"],
                                "team_color": team_color,
                                "agentIcon": agentIcon,
                                "agentName": agentName,
                                "name": name,
                                "cur_rank": cur_rank,
                                "cur_s": cur_s,
                                "rank_icon": rank_icon,
                                "win": win,
                                "kd": kd,
                                "head": head,
                                "skinIcon": skinIcon,
                                "skinName": skinName,
                                "peak_rank": peak_rank,
                                "peak_name": peak_name,
                                "peak_icon": peak_icon,
                                "shields": mmr["DerankProtectedGamesRemaining"],
                                "shield_stats": mmr["DerankProtectedStatus"]
                            }
                        )

                        current_loaded += 1
                        #                        os.system("cls")
                        print(f"Loaded [{current_loaded}/{player_count}]")

        def liveviewGui(skinData=None):
            if self.game_state == "MENUS":  # メニュー
                return ft.Container(
                    content=ft.Text("Waiting for the next game", size=40),
                    alignment=ft.alignment.center,
                    expand=True,
                )

            elif self.game_state == "PREGAME":  # エージェント選択画面
                pregameID = self.util.api.get_current_pregame_id()
                if pregameID != None:
                    game = self.util.api.get_pregame_status(pregameID)
                    gui = ft.Container(
                        alignment=ft.alignment.center, margin=ft.margin.only(left=15)
                    )
                    column = ft.Column(
                        [],
                        alignment=ft.MainAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.ALWAYS,
                        height=page.height - 142,
                        spacing=15,
                    )
                    players = game["AllyTeam"]["Players"]
                    names = {
                        player["Subject"]: f"{player['GameName']}#{player['TagLine']}"
                        for player in self.util.api.get_user_names(
                            [p["Subject"] for p in players]
                        )
                    }

                    column.controls.append(
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Row(
                                            [
                                                ft.Text("Agent", size=20),
                                                ft.Text("Name", size=20),
                                            ],
                                            spacing=35,
                                        ),
                                        ft.Row(
                                            [
                                                ft.Text("Rank", size=20),
                                                ft.Text("Win%", size=20),
                                                ft.Text("K/D", size=20),
                                                ft.Text("HS%", size=20),
                                                ft.Text("Peak", size=20),
                                            ],
                                            spacing=55,
                                        ),
                                    ],
                                    spacing=170,
                                ),
                                ft.Container(
                                    content=ft.Divider(),
                                    margin=ft.margin.only(left=-105),
                                ),
                            ],
                        )
                    )

                    player_count = len(players)
                    current_loaded = 0
                    for player in players:
                        name = names[player["Subject"]]
                        agentID = player["CharacterID"]
                        state = player["CharacterSelectionState"]
                        hasSelect = True if len(state) > 5 else False
                        agentIcon = "https://i.ibb.co/wFTQwPtK/image.png"
                        agentName = "None"

                        if hasSelect:
                            res = requests.get(
                                f"https://valorant-api.com/v1/agents/{agentID}"
                            ).json()["data"]
                            agentName = res["displayName"]
                            agentIcon = res["displayIcon"]
                        team_color = "#181c22"

                        if self.has_got_liveview == False:
                            mmr = None
                            while mmr is None:
                                mmr_res = self.api.api.get_player_mmr(player["Subject"])
                                if mmr_res.get("code") is None:
                                    mmr = mmr_res
                                    break
                                time.sleep(2)

                            nowseason = self.api.get_active_season()[0]
                            season = nowseason["uuid"]

                            rank_icon = "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/0/smallicon.png"
                            cur_season_rank = 0
                            cur_s = None
                            seasons = None
                            peak = 0
                            win = 0
                            head = 0
                            peak_season_info = self.api.api.get_competitive_season(
                                self.api.get_active_season()[0]["uuid"]
                            )
                            peak_name = (
                                re.search(
                                    r"CompetitiveSeason_(.*?)_DataAsset",
                                    peak_season_info["assetPath"],
                                )
                                .group(1)
                                .replace("_", " ")
                                .replace("-1", "")
                                .replace("EpisodeV", "V")
                            )

                            rankList = requests.get(
                                "https://valorant-api.com/v1/competitivetiers"
                            ).json()["data"][-1]["tiers"]
                            if mmr.get("QueueSkills") is not None:
                                rankInfo = mmr["QueueSkills"]["competitive"][
                                    "SeasonalInfoBySeasonID"
                                ]
                                if rankInfo is not None:
                                    seasons = [
                                        {"id": k, **v} for k, v in rankInfo.items()
                                    ]
                                    seasons.sort(key=lambda x: x["Rank"], reverse=True)
                                    peak = seasons[0]["Rank"]
                                    peak_season_id = seasons[0]["id"]
                                    peak_season_info = (
                                        self.api.api.get_competitive_season(
                                            peak_season_id
                                        )
                                    )
                                    peak_name = (
                                        re.search(
                                            r"CompetitiveSeason_(.*?)_DataAsset",
                                            peak_season_info["assetPath"],
                                        )
                                        .group(1)
                                        .replace("_", " ")
                                        .replace("-1", "")
                                        .replace("EpisodeV", "V")
                                    )

                                    cur_s = rankInfo.get(season)
                                    if cur_s is not None:
                                        cur_season_rank = (
                                            cur_s["CompetitiveTier"]
                                            if cur_s is not None
                                            else 0
                                        )
                                        win = math.floor(
                                            (
                                                cur_s["NumberOfWins"]
                                                / cur_s["NumberOfGames"]
                                            )
                                            * 100
                                        )
                            _history = self.api.api.get_match_history(
                                player["Subject"], "competitive", start=0, end=3
                            )
                            if _history.get("History") is not None:
                                history = _history.get("History")
                                total_hit = 0
                                head_hit = 0
                                kills = 0
                                deaths = 1
                                kd = 0.00

                                for h2 in history:
                                    id = h2["MatchID"]
                                    detail = self.api.api.get_match_details(id)
                                    if detail.get("roundResults") is not None:
                                        info = detail["roundResults"]

                                        me_stats = self.api.find_obj(
                                            lambda x: x["subject"] == player["Subject"],
                                            detail["players"],
                                        )[0]["stats"]
                                        kills += me_stats["kills"]
                                        deaths += me_stats["deaths"]

                                for h in history[0:2]:
                                    id = h["MatchID"]
                                    detail = self.api.api.get_match_details(id)
                                    if detail.get("roundResults") is not None:
                                        info = detail["roundResults"]

                                        me_stats = self.api.find_obj(
                                            lambda x: x["subject"] == player["Subject"],
                                            detail["players"],
                                        )[0]["stats"]
                                        kills += me_stats["kills"]
                                        deaths += me_stats["deaths"]

                                        for _round in info:
                                            p_stats = _round["playerStats"]
                                            me = self.api.find_obj(
                                                lambda x: x["subject"]
                                                == player["Subject"],
                                                p_stats,
                                            )[0]
                                            me_dmg = me["damage"]

                                            for dmg in me_dmg:
                                                total_hit += dmg["bodyshots"]
                                                total_hit += dmg["legshots"]
                                                total_hit += dmg["headshots"]
                                                head_hit += dmg["headshots"]
                            head = math.floor(
                                (head_hit / total_hit if total_hit > 0 else 1) * 100
                            )
                            kd = round(kills / deaths if deaths > 0 else 1, 2)

                            cur_rank = self.api.find_obj(
                                lambda x: x["tier"] == cur_season_rank, rankList
                            )[0]
                            peak_rank = self.api.find_obj(
                                lambda x: x["tier"] == peak, rankList
                            )[0]
                            rank_icon = cur_rank["smallIcon"]
                            peak_icon = peak_rank["smallIcon"]

                            column.controls.append(
                                ft.Row(
                                    [
                                        ft.Row(
                                            [
                                                ft.Stack(
                                                    controls=[
                                                        ft.Container(
                                                            bgcolor=team_color,
                                                            width=45,
                                                            height=45,
                                                            border_radius=10,
                                                            content=ft.Image(
                                                                agentIcon,
                                                                border_radius=10,
                                                                width=45,
                                                                height=45,
                                                                tooltip=ft.Tooltip(
                                                                    message=agentName,
                                                                    bgcolor=ft.colors.TRANSPARENT,
                                                                    text_style=ft.TextStyle(
                                                                        color=ft.colors.WHITE
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ],
                                                    width=60,
                                                ),
                                                ft.Text(
                                                    name.split("#")[0][:6] + "...",
                                                    size=21,
                                                    width=130,
                                                    color=ft.colors.WHITE,
                                                    tooltip=ft.Tooltip(
                                                        message=name,
                                                        bgcolor=ft.colors.TRANSPARENT,
                                                        text_style=ft.TextStyle(
                                                            color=ft.colors.WHITE
                                                        ),
                                                    ),
                                                ),
                                            ],
                                            spacing=30,
                                        ),
                                        ft.Row(
                                            [
                                                ft.Container(
                                                    ft.Image(
                                                        rank_icon,
                                                        width=45,
                                                        height=45,
                                                        tooltip=ft.Tooltip(
                                                            f"{cur_rank['tierName']}({cur_s['RankedRating'] if cur_s is not None else 0}RR)\nShield: {mmr['DerankProtectedGamesRemaining']} ({mmr['DerankProtectedStatus']})",
                                                            bgcolor=ft.colors.TRANSPARENT,
                                                            text_style=ft.TextStyle(
                                                                color=ft.colors.WHITE
                                                            ),
                                                        ),
                                                    ),
                                                    width=105,
                                                ),
                                                ft.Text(f"{win}%", size=20, width=67),
                                                ft.Text(f"{kd}", size=20, width=65),
                                                ft.Text(f"{head}%", size=20, width=65),
                                                ft.Image(
                                                    peak_icon,
                                                    width=45,
                                                    height=45,
                                                    tooltip=ft.Tooltip(
                                                        f"{peak_rank['tierName']} / {peak_name}",
                                                        bgcolor=ft.colors.TRANSPARENT,
                                                        text_style=ft.TextStyle(
                                                            color=ft.colors.WHITE
                                                        ),
                                                    ),
                                                ),
                                            ],
                                            spacing=30,
                                        ),
                                    ],
                                    spacing=63,
                                ),
                            )
                            current_loaded += 1
                            os.system("cls")
                            print(f"Loaded [{current_loaded}/{player_count}]")
                    gui.content = column
                    return gui
                    # return ft.Container(
                    #     content=ft.Text(json.dumps(players[0]), size=20),
                    #     alignment=ft.alignment.center,
                    #     expand=True,
                    # )

            elif self.game_state == "INGAME":  # 試合
                while True:
                    try:
                        gameID = self.util.api.get_current_match_id()
                        break
                    except:
                        pass
                    time.sleep(2)
                if gameID != None:
                    if self.liveview_Data.get("id") != gameID:
                        get_liveview_data_ingame()
                    gui = ft.Container(
                        alignment=ft.alignment.center, margin=ft.margin.only(left=15)
                    )
                    column = ft.Column(
                        [],
                        alignment=ft.MainAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.ALWAYS,
                        height=page.height - 142,
                        spacing=15,
                    )

                    column.controls.append(get_menubar())

                    all_players = self.liveview_Data["players"]

                    for player in all_players:
                        skinInfo = None
                        if skinData is not None:
                            weapons = requests.get(
                                f"https://valorant-api.com/v1/weapons"
                            ).json()
                            vandal_info = self.api.find_obj(
                                lambda x: x["uuid"]
                                == self.weaponsMap[self.currentWeapon],
                                weapons["data"],
                            )[0]
                            skin = self.api.find_obj(
                                lambda x: x["uuid"]
                                == skinData[player["Subject"]]["id"],
                                vandal_info["skins"],
                            )[0]
                            obj = self.api.find_obj(
                                lambda x: x["uuid"]
                                == skinData[player["Subject"]]["chroma"],
                                skin["chromas"],
                            )[0]

                        column.controls.append(
                            ft.Row(
                                [
                                    ft.Row(
                                        [
                                            ft.Stack(
                                                controls=[
                                                    ft.Container(
                                                        bgcolor=player["team_color"],
                                                        width=45,
                                                        height=45,
                                                        border_radius=10,
                                                        content=ft.Image(
                                                            player["agentIcon"],
                                                            border_radius=10,
                                                            width=45,
                                                            height=45,
                                                            tooltip=ft.Tooltip(
                                                                message=player[
                                                                    "agentName"
                                                                ],
                                                                bgcolor=ft.colors.TRANSPARENT,
                                                                text_style=ft.TextStyle(
                                                                    color=ft.colors.WHITE
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ],
                                                width=60,
                                            ),
                                            ft.Text(
                                                player["name"].split("#")[0][:6]
                                                + "...",
                                                size=21,
                                                width=130,
                                                color=ft.colors.WHITE,
                                                tooltip=ft.Tooltip(
                                                    message=player["name"],
                                                    bgcolor=ft.colors.TRANSPARENT,
                                                    text_style=ft.TextStyle(
                                                        color=ft.colors.WHITE
                                                    ),
                                                ),
                                            ),
                                        ],
                                        spacing=30,
                                    ),
                                    ft.Row(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Container(
                                                        ft.Image(
                                                            player["rank_icon"],
                                                            width=45,
                                                            height=45,
                                                            tooltip=ft.Tooltip(
                                                                f"{player['cur_rank']['tierName']}({player['cur_s']['RankedRating'] if player['cur_s'] is not None else 0}RR)\nShield: {player['shields']} ({player['shield_stats']})",
                                                                bgcolor=ft.colors.TRANSPARENT,
                                                                text_style=ft.TextStyle(
                                                                    color=ft.colors.WHITE
                                                                ),
                                                            ),
                                                        ),
                                                        width=105,
                                                    ),
                                                    ft.Text(
                                                        f"{player['win']}%",
                                                        size=20,
                                                        width=67,
                                                    ),
                                                    ft.Text(
                                                        f"{player['kd']}",
                                                        size=20,
                                                        width=65,
                                                    ),
                                                    ft.Text(
                                                        f"{player['head']}%",
                                                        size=20,
                                                        width=65,
                                                    ),
                                                    ft.Image(
                                                        player["peak_icon"],
                                                        width=45,
                                                        height=45,
                                                        tooltip=ft.Tooltip(
                                                            f"{player['peak_rank']['tierName']} / {player['peak_name']}",
                                                            bgcolor=ft.colors.TRANSPARENT,
                                                            text_style=ft.TextStyle(
                                                                color=ft.colors.WHITE
                                                            ),
                                                        ),
                                                    ),
                                                ],
                                                spacing=30,
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Image(
                                                        (
                                                            obj["fullRender"]
                                                            if skinData is not None
                                                            else player["skinIcon"]
                                                        ),
                                                        tooltip=ft.Tooltip(
                                                            (
                                                                obj["displayName"]
                                                                if skinData is not None
                                                                else player["skinName"]
                                                            ),
                                                            bgcolor=ft.colors.TRANSPARENT,
                                                            text_style=ft.TextStyle(
                                                                color=ft.colors.WHITE
                                                            ),
                                                        ),
                                                        height=50,
                                                        width=200,
                                                    ),
                                                ]
                                            ),
                                        ],
                                        spacing=40,
                                    ),
                                ],
                                spacing=63,
                            ),
                        )
                    gui.content = column
                    return gui

        # OverViewのgui
        def updateOverView():
            self.current = 0
            self.total = 0

            if self.view_name == "overview":
                content_area.controls.clear()
                page.update()
                content_area.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Fetching data...", size=30),
                                ft.Text(
                                    f"{str(self.current)}/{str(self.total)} ready",
                                    size=20,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                        expand=True,
                    )
                )
            page.update()
            # ここでいろいろなパラメーターを更新
            get_overview_data()
            #
            page.controls.clear()
            content_area.controls.clear()
            content_area.controls.append(overviewGui())
            footer.controls.clear()
            footer.controls.extend(
                [
                    ft.Column(
                        [
                            ft.TextButton(
                                content=ft.Text("Over View"),
                                on_click=lambda _: switch_view("overview"),
                            ),
                            ft.Container(
                                height=1,
                                width=90,
                                bgcolor=(
                                    ft.colors.BLUE
                                    if self.view_name == "overview"
                                    else ft.colors.TRANSPARENT
                                ),
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Text(" | "),  # 区切り
                    ft.Column(
                        [
                            ft.TextButton(
                                content=ft.Text("Live View"),
                                on_click=lambda _: switch_view("liveview"),
                            ),
                            ft.Container(
                                height=1,
                                width=90,
                                bgcolor=(
                                    ft.colors.BLUE
                                    if self.view_name == "liveview"
                                    else ft.colors.TRANSPARENT
                                ),
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Text(" | "),  # 区切り
                    ft.Column(
                        [
                            ft.TextButton(
                                content=ft.Text("Match History"),
                                on_click=lambda _: switch_view("matchhistory"),
                            ),
                            ft.Container(
                                height=1,
                                width=90,
                                bgcolor=(
                                    ft.colors.BLUE
                                    if self.view_name == "matchhistory"
                                    else ft.colors.TRANSPARENT
                                ),
                            ),
                        ],
                        spacing=2,
                    ),
                ]
            )
            page.controls.append(
                ft.Column(
                    controls=[
                        ft.Container(content_area, expand=True),
                        ft.Divider(),
                        footer,
                    ],
                    expand=True,
                )
            )
            page.update()

        def updateLiveView(skinData=None):
            # 更新

            #
            gui = liveviewGui(skinData)
            if type(gui) is not type(None):
                content_area.controls.clear()
                content_area.controls.append(gui)
            page.update()

        # ゲームモード変更 (overviewとmatchhistoryで使いまわす予定)
        def change_gamemode():
            if self.view_name == "overview":
                # ["unrated", "competitive", "swiftplay", "deathmatch", "hurm"]
                content_area.controls.clear()
                content_area.controls.append(overviewGui())
                page.update()

        def update_weaponstate():
            self.currentWeapon = weaponDD.value
            weaponID = self.weaponsMap[self.currentWeapon]
            self.skins = {}
            for weapon in self.loadout_cache["Loadouts"]:
                p_loadout = weapon["Loadout"]
                pid = p_loadout["Subject"]
                if len(pid) > 0:
                    skinID = p_loadout["Items"][weaponID]["Sockets"][
                        "bcef87d6-209b-46c6-8b19-fbe40bd95abc"
                    ]["Item"]["ID"]
                    self.skins.update(
                        {
                            pid: {
                                "chroma": p_loadout["Items"][weaponID]["Sockets"][
                                    "3ad1b2b2-acdb-4524-852f-954a76ddae0a"
                                ]["Item"]["ID"],
                                "id": skinID,
                            }
                        }
                    )
            updateLiveView(self.skins)

        weaponDD = ft.Dropdown(
            label="Select weapon",
            autofocus=True,
            hint_text="Select weapon",
            options=[
                ft.dropdown.Option(data["displayName"])
                for data in requests.get("https://valorant-api.com/v1/weapons").json()[
                    "data"
                ]
            ],
            value="Vandal",
            width=140,
            content_padding=ft.Padding(top=13, bottom=13, left=10, right=0),
            border_color="#181c22",
            bgcolor="#181c22",
            on_change=lambda _: update_weaponstate(),
            enable_filter=True
        )

        def get_menubar():
            bar = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Text("Agent", size=20),
                                    ft.Text("Name", size=20),
                                ],
                                spacing=35,
                            ),
                            ft.Row(
                                [
                                    ft.Text("Rank", size=20),
                                    ft.Text("Win%", size=20),
                                    ft.Text("K/D", size=20),
                                    ft.Text("HS%", size=20),
                                    ft.Text("Peak", size=20),
                                    ft.Row(
                                        [ft.Text("Weapon", size=20), weaponDD],
                                        spacing=20,
                                    ),
                                ],
                                spacing=55,
                            ),
                        ],
                        spacing=170,
                    ),
                    ft.Container(
                        content=ft.Divider(),
                        margin=ft.margin.only(left=-105),
                    ),
                ],
            )
            return bar

        def clean_controls(ctrl):
            if hasattr(ctrl, "controls") and isinstance(ctrl.controls, list):
                ctrl.controls = [c for c in ctrl.controls if c is not None]
            for c in ctrl.controls:
                clean_controls(c)

        def update_state():
            while True:
                presence = self.util.api.wait_presence()
                new = self.util.api.get_game_state(presence)
                self.api.api.presense = new
                if self.api.api.puuid is None:
                    self.api.api.puuid = self.api.api.get_current_player_puuid()

                if self.view_name == "liveview" and self.game_state == "PREGAME":
                    updateLiveView()

                if self.game_state != "INGAME" and new == "INGAME":
                    self.lastMatchID = self.api.api.get_current_match_id()

                if self.game_state == "INGAME" and new != "INGAME":
                    lastData = self.api.api.get_match_details(self.lastMatchID)
                    if lastData.get("code") not in (400, 401, 404, 403):
                        self.api.encrypt_and_save(lastData)

                if self.game_state != new:
                    self.game_state = new
                    changed_state(new)
                time.sleep(7)

        # Stateが変わったら発火する
        def changed_state(new_state):
            if self.view_name == "liveview":
                updateLiveView()

        threading.Thread(target=update_state, daemon=True).start()

        # ゲームモード drop down (overview用)
        box_height = 415  # boxの高さ
        box_width = page.width / 3.65  # dropdownとboxのサイズ
        drop = ft.Dropdown(
            label="Select game mode",
            autofocus=True,
            hint_text="Select game mode",
            options=[
                ft.dropdown.Option("Unrated"),
                ft.dropdown.Option("Competitive"),
                ft.dropdown.Option("Swiftplay"),
                ft.dropdown.Option("Deathmatch"),
                ft.dropdown.Option("Team Deathmatch"),
            ],
            value="Unrated",
            width=box_width,
            border_color="#181c22",
            bgcolor="#181c22",
            on_change=lambda _: change_gamemode(),
        )

        # フッター部分（ウィンドウの一番下）
        footer = ft.Row(alignment=ft.MainAxisAlignment.CENTER)

        # ページ切り替え関数 - ここにメインの描画処理
        def switch_view(view_name: str):
            if self.view_name == view_name:
                return
            content_area.controls.clear()
            self.view_name = view_name
            self.current = 0
            self.total = 0
            updateFooter()
            if view_name == "overview":  # ユーザープロフィール
                if all(self.overview.get(key) is None for key in self.overview.keys()):
                    get_overview_data()
                content_area.controls.clear()
                content_area.controls.append(overviewGui())
                page.controls.clear()
                page.add(
                    ft.Column(
                        controls=[
                            ft.Container(content_area, expand=True),
                            ft.Divider(),
                            footer,
                        ],
                        expand=True,
                    )
                )

            elif view_name == "liveview":  # 試合の情報
                content_area.controls.clear()
                content_area.controls.append(liveviewGui())
                page.controls.clear()
                page.add(
                    ft.Column(
                        controls=[
                            ft.Container(content_area, expand=True),
                            ft.Divider(),
                            footer,
                        ],
                        expand=True,
                    )
                )
            elif view_name == "matchhistory":  # 試合履歴
                content_area.controls.clear()
                content_area.controls.append(ft.Column([ft.Text("しあいりれき")]))
                page.controls.clear()
                page.add(
                    ft.Column(
                        controls=[
                            ft.Container(content_area, expand=True),
                            ft.Divider(),
                            footer,
                        ],
                        expand=True,
                    )
                )
            page.update()

        # 初期表示
        switch_view("overview")

        # 全体レイアウト
        page.controls.clear()
        page.add(
            ft.Column(
                controls=[
                    ft.Container(content_area, expand=True),
                    ft.Divider(),
                    footer,
                ],
                expand=True,
            )
        )

    def __init__(self):
        self.api = utils()
        self.page = None  # fletのページ
