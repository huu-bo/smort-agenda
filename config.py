import json


class Config:
    def __init__(self, raw):
        if raw is None:
            self.background_url = None
            self.lines = True
            self.appointment_background = True
        else:
            background = raw.get('background', {'scale': False, 'url': None})
            self.background_url = background.get('url', None)
            self.background_scale = background.get('scale', False)

            self.lines = raw.get('lines', True)
            self.appointment_background = raw.get('appointment_background', True)


try:
    with open('config.json', 'r') as file:
        config = Config(json.load(file))
except FileNotFoundError:
    config = Config(None)
