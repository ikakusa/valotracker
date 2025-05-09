from pyvaloapi.client_mod import ValorantClient
import numpy as np
import requests as req
from datetime import datetime, timezone
from pyvaloapi.classes.User import User, Account, Pw
import os
import os.path as path
import json
import uuid
import math
from collections import defaultdict

class utils:
    def __init__(self):
        self.client = ValorantClient()
        self.api = self.client.unofficial_api()
        self.player = self.api.get_current_player()
        self.user = User(self.player)

    #配列から特定のjsonを取得する
    def find_obj(self, func, listobj):
        return list(filter(func, listobj))
    
    def get_username(self) -> str:
        usr = self.user.acct
        return f"{usr.gamename}#{usr.tag_line}"
    
    def get_previous_season(self):
        all_seasons = self.get_all_seasons()
        
        try:
            cur_season_i = all_seasons.index(self.get_active_season()[0])
        except:
            return None
        cur_season_i = 1 if cur_season_i == 0 else cur_season_i

        return all_seasons[cur_season_i - 1]

    def get_active_season(self):
        # seasonのリスト取得
        res = req.get("https://valorant-api.com/v1/seasons")
        
        if res.status_code != 200: return None
        data = res.json()
        now = datetime.now(timezone.utc)
        active_seasons = []
        for season in data.get("data", []):
            start = season.get("startTime")
            end = season.get("endTime")
            if not start or not end: continue
            # actの開始時間/終了時間
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(timezone.utc)
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")).astimezone(timezone.utc)
            if start_dt <= now <= end_dt:
                # 前のep/actを取得するためにリストにしとく
                active_seasons.append({
                    "uuid": season.get("uuid"),
                    "displayName": season.get("title"),
                    "startTime": start_dt,
                    "endTime": end_dt
                })
        return active_seasons if active_seasons else None
    
    def get_all_seasons(self):
        # seasonのリスト取得
        res = req.get("https://valorant-api.com/v1/seasons")
        
        if res.status_code != 200: return None
        data = res.json()
        seasons = []
        for season in data.get("data", []):
            start = season.get("startTime")
            end = season.get("endTime")
            if not start or not end: continue
            # actの開始時間/終了時間
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(timezone.utc)
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")).astimezone(timezone.utc)
            seasons.append({
                "uuid": season.get("uuid"),
                "displayName": season.get("title"),
                "startTime": start_dt,
                "endTime": end_dt
            })
        return seasons if seasons else None

    def get_userid(self):
        try:
            return self.api.get_current_player_puuid()
        except:
            return self.api.puuid
    # Folder
    def get_appdata(self):
        return os.getenv("LOCALAPPDATA")
    def get_app_folder(self):
        a_path = f"{self.get_appdata()}\\ValoTracker"
        if not path.exists(a_path):
            os.mkdir(f"{a_path}")
        return a_path
    def create_history_folder(self):
        me_id = self.api.puuid
        a_path = self.get_app_folder()
        if not path.exists(f"{a_path}\\History"):
            os.mkdir(f"{a_path}\\History")
        if not path.exists(f"{a_path}\\History\\{me_id}"):
            os.mkdir(f"{a_path}\\History\\{me_id}")
    def check_history_exist(self):
        me_id = self.api.puuid
        a_path = self.get_app_folder()
        if not path.exists(f"{a_path}"):
            os.mkdir(f"{a_path}")
        if not path.exists(f"{a_path}\\History"):
            os.mkdir(f"{a_path}\\History")
        if not path.exists(f"{a_path}\\History\\{me_id}"):
            os.mkdir(f"{a_path}\\History\\{me_id}")

        count = 0
        for file in os.scandir(f"{a_path}\\History\\{me_id}"):
            if file.is_file() and file.name.split(".")[-1] == "hist":
                count+=1
        if count <= 0:
            return False
        return True

    def get_histories(self):
        me_id = self.api.puuid
        a_path = self.get_app_folder()
        histories = []
        self.check_history_exist()
        for file in os.scandir(f"{a_path}\\History\\{me_id}"):
            if file.is_file() and file.name.split(".")[-1] == "hist":
                histories.append({ "name": file.name, "date": path.getmtime(file.path) })
        all = histories
        if all is None:
            return None
        result = defaultdict(list)
        for hist in all:
            hist_data = self.decrypt_history(hist["name"])
            result[hist_data["matchInfo"]["queueID"]].append({"id": hist["name"], "date": path.getctime(f"{a_path}\\History\\{me_id}\\{hist['name']}")})

        for k, v in result.items():
            result[k] = sorted(v, key=lambda x: x["date"], reverse=True)
        return result
    
    #need extension like this: {uuid}.hist
    def decrypt_history(self, name):
        me_id = self.api.puuid
        self.check_history_exist()
        h_path = f"{self.get_app_folder()}\\History\\{me_id}\\{name}"
        if not path.exists(h_path):
            return None
        with open(h_path, "rb") as r:
            bytes_data = r.read()
        codes = 0
        for t in name:
            codes += ord(t)
        codes = math.floor((255 / codes) * 1000)
        codes = codes if codes < 256 else 255

        decrypted = bytes(b ^ codes for b in bytes_data)
        return json.loads(decrypted.decode())
    
    def update_history(self):
        self.check_history_exist()
        me_id = self.api.puuid
        all = self.get_histories()
        if all is None:
            return
        result = all

        for k, v in result.items():
            if len(result[k]) < 50:
                return
            OLD = result[k][49:]
            for h in OLD:
                a_path = f"{self.get_app_folder()}\\History\\{me_id}\\{v['name']}"
                if path.exists(a_path):
                    os.remove(a_path)

    def encrypt_and_save(self, obj):
        self.check_history_exist()
        me_id = self.api.puuid
        a_path = f"{self.get_app_folder()}\\History\\{me_id}"
        data = json.dumps(obj)
        file_id = uuid.uuid1()
        name = f"{file_id}.hist"
        encoded = data.encode()
        codes = 0
        for t in name:
            codes += ord(t)
        codes = math.floor((255 / codes) * 1000)
        codes = codes if codes < 256 else 255
        with open(f"{a_path}\\{name}", "wb") as wb:
            wb.write(bytes(b ^ codes for b in encoded))
        self.update_history()
        return { "name": name }