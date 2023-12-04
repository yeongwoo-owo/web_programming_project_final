class DuplicateUserException(Exception):
    def __init__(self, login_id):
        super().__init__(f'중복된 Login Id가 존재합니다. Login ID: {login_id}')

    @staticmethod
    def description():
        return "중복된 ID가 존재합니다."


class LoginException(Exception):
    def __init__(self):
        super().__init__(f'입력하신 정보와 일치하는 유저가 존재하지 않습니다.')

    @staticmethod
    def description():
        return "입력하신 정보와 일치하는 유저가 존재하지 않습니다."


class SessionNotFoundException(Exception):
    def __init__(self, session_id):
        super().__init__(f'세션 ID에 해당하는 유저가 존재하지 않습니다. 세션 ID: {session_id}')
        