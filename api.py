import threading
import requests
import urllib.parse
from datetime import datetime


class Appointment:
    def __init__(self, raw: dict):
        self.valid = True

        if 'subjects' not in raw:
            self.valid = False
            return
        else:
            self.subjects = raw['subjects']
        # groups, locations, teachers, cancelled, online, start, end
        
        if 'groups' not in raw:
            self.valid = False
            return
        else:
            self.groups = raw['groups']
        
        if 'locations' not in raw:
            self.valid = False
            return
        else:
            self.locations = raw['locations']

        if 'teachers' not in raw:
            self.valid = False
            return
        else:
            self.teachers = raw['teachers']

        if 'cancelled' not in raw:
            self.valid = False
            return
        else:
            self.cancelled = raw['cancelled']
        
        if 'online' not in raw:
            self.valid = False
            return
        else:
            self.online = raw['online']
        
        if 'start' not in raw:
            self.valid = False
            return
        else:
            # time = datetime.fromtimestamp(int(raw['start'])).strftime('%j %H:%M:%S').split(' ')
            # self.start = (int(time[0]), [int(t) for t in time[1].split(':')])
            self.start = datetime.fromtimestamp(raw['start'])
        
        if 'end' not in raw:
            self.valid = False
            return
        else:
            # time = datetime.fromtimestamp(int(raw['end'])).strftime('%j %H:%M:%S').split(' ')
            # self.end = (int(time[0]), [int(t) for t in time[1].split(':')])
            self.end = datetime.fromtimestamp(raw['end'])
            

class Week:
    def __init__(self, raw: dict, week: int):
        self.week = week
        self.raw = raw

        self.valid = True
        self.appointments = []

        if 'response' not in self.raw:
            print('no response?')
            self.valid = False
            return

        if 'data' not in self.raw['response']:
            print('no response data?')
            self.valid = False

        if len(self.raw['response']['data']) != 1:
            raise NotImplementedError('multiple weeks in one week')

        week = self.raw['response']['data'][0]

        if 'appointments' not in week:
            print('no appointments in week')
            self.valid = False
            return

        for appointment in week['appointments']:
            self.appointments.append(Appointment(appointment))


class Api:
    def __init__(self, username, password, tenant):
        self.username = username
        self.password = password
        self.tenant = tenant

        self.zportal_url = f'https://{self.tenant}.zportal.nl'
        self.api_url = f'{self.zportal_url}/api/v3/'

        self.state = 0
        self.max_state = 3

        self.successfull = True
        self.credentials_correct = True

        self.queue = []
        self.busy = False
        self.weeks = {}

        self.t = threading.Thread(target=self._bootstrap)
        self.t.start()

    def _bootstrap(self):
        r = requests.get(self.api_url + 'oauth')
        print(r.status_code)
        if r.status_code != 200:
            self.successfull = False  # TODO: error message
            return

        self.jar = r.cookies

        content = r.content.decode('utf-8')

        redirect_search = '<input name="redirect_uri" type="hidden" value='
        redirect_index = content.find(redirect_search)
        redirect = ''
        i = redirect_index + len(redirect_search) + 1
        while content[i] != '"':
            redirect += content[i]
            i += 1

        state_search = '<input name="state" type="hidden" value='
        state_index = content.find(state_search)
        state = ''
        i = state_index + len(state_search) + 1
        while content[i] != '"':
            state += content[i]
            i += 1

        self.state += 1

        r = requests.post(self.api_url + 'oauth', data={
            'username': self.username,
            'password': self.password,
            'client_id': 'OAuthPage',
            'redirect_uri': redirect,
            'scope': '',
            'state': state,
            'response_type': 'code',
            'tenant': 'ig'
        }, cookies=self.jar)

        print(r.status_code)
        if r.status_code != 200:
            self.successfull = False  # TODO: error message
            return

        content = r.content.decode('utf-8')

        path_search = '<a href='
        path_index = content.find(path_search)
        path = ''
        i = path_index + len(path_search) + 1
        while content[i] != '"':
            path += content[i]
            i += 1

        parsed_path = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)

        if 'code' not in parsed_path:
            self.credentials_correct = False
            self.successfull = False
            return

        if len(parsed_path['code']) != 1:
            print('WARNING: multiple codes')
        code = parsed_path['code'][0]

        if len(parsed_path['interfaceVersion']) != 1:
            print('WARNING: multiple versions')
        if parsed_path['interfaceVersion'][0] != '23.03j57':
            print('WARNING: unsupported version')

        if len(parsed_path['tenant']) != 1:
            print('WARNING: multiple tenants?')
        if parsed_path['tenant'][0] != self.tenant:
            print(f'WARNING: tenant {self.tenant} not {parsed_path["tenant"][0]}')

        self.state += 1

        r = requests.post(self.api_url + 'oauth/token', cookies=self.jar, data={
            'code': code,
            'client_id': 'ZermeloPortal',
            'client_secret': 42,  # TODO: ??
            'grant_type': 'authorization_code',
            'rememberMe': 'false'
        })

        print(r.status_code)
        if r.status_code != 200:
            self.successfull = False  # TODO: error message
            return

        token_raw = r.json()
        self.token = token_raw['access_token']
        if token_raw['token_type'] != 'bearer':
            print('WARNING: unsupported token type')

        self.state += 1

        self.busy = False

    def update(self):
        if self.t.is_alive():
            return

        if not self.busy:
            self.t.join()

        if len(self.queue) > 0:
            self.t = threading.Thread(target=self._get, args=[self.queue.pop(0)])
            self.t.start()
            self.busy = True

    def get(self, week):
        # print(f'get {week} in? {week in self.weeks} busy? {self.busy}')
        if week in self.weeks:
            return self.weeks[week]

        if self.busy or self.t.is_alive():
            if week in self.queue or week in self.weeks:
                return
            self.queue.append(week)
            return None  # TODO: store empty week

        self.t = threading.Thread(target=self._get, args=[week])
        self.t.start()
        return None

    def _get(self, week):
        self.busy = True

        url = self.api_url + 'liveschedule?' + urllib.parse.urlencode({
            'student': self.username,
            'week': str(week),
            'fields': 'appointmentInstance,start,end,startTimeSlotName,endTimeSlotName,subjects,groups,locations,teachers,cancelled,changeDescription,schedulerRemark,content,appointmentType,creator'
        })

        r = requests.get(url, cookies=self.jar, auth=('Bearer', self.token))
        print(r.status_code)
        if r.status_code != 200:
            self.busy = False

            print(url)
            print(r.content.decode('utf-8'))
            print(week)

            return  # TODO: print error

        try:
            self.weeks[week] = Week(r.json(), week)
        except requests.exceptions.JSONDecodeError as e:
            print(e)
            print(url)
            self.busy = False
            return
