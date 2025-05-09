from datetime import datetime

class Account:
    def __init__(self, acct_data):
        self.acct = acct_data
        self.type = self.acct.get('type')
        self.state = self.acct.get('state')
        self.adm = self.acct.get('adm')
        self.gamename = self.acct.get('game_name')
        self.tag_line = self.acct.get('tag_line')
        self.created_at = self.convert_timestamp(self.acct.get('created_at'))

    def convert_timestamp(self, timestamp):
        if timestamp:
            return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        return None

class Pw:
    def __init__(self, pw_data):
        self.pw = pw_data
        self.changed_at = self.convert_timestamp(self.pw.get('cng_at'))
        self.reset = self.pw.get('reset')
        self.must_reset = self.pw.get('must_reset')

    def convert_timestamp(self, timestamp):
        if timestamp:
            return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        return None

class User:
    def __init__(self, user_data):
        self.user = user_data
        self.pw = Pw(self.user.get('pw'))
        self.acct = Account(self.user.get('acct'))
        self.country = self.user.get('country')
        self.uuid = self.user.get('sub')
        self.email_verified = self.user.get('email_verified')
        self.phone_verified = self.user.get('phone_verified')
        self.player_plocale = self.user.get('player_plocale')
        self.username = self.user.get('username')
        self.country_at = self.convert_timestamp(self.user.get('country_at'))

    def convert_timestamp(self, timestamp):
        if timestamp:
            return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        return None