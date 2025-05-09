from pyvaloapi.local_api import UnofficialAPI

class ValorantClient:
	def __init__(self):
		pass
	

	def unofficial_api(self):
		return UnofficialAPI.init_from_lockFile()
