import requests
from datetime import datetime
from time import time


HQ_URL = 'https://api-quiz.hype.space/'
HQ_REQUEST_HEADERS = {'x-hq-client': 'Android/1.40.0'}


class HQResponseError(Exception):
    """Raise when the HQ verifications endpoint returns an error code."""


def hq_post(endpoint, data):
    resp = requests.post(f'{HQ_URL}{endpoint}',
                         headers=HQ_REQUEST_HEADERS,
                         data=data).json()

    if 'errorCode' in resp:
        raise HQResponseError(f'Error code {resp["errorCode"]}: {resp["error"]}')

    return resp


def main():
    print('Enter your phone number, including + and country code (e.g. +14155552671)')
    print('Example: (415) 555-0171 (U.S. number) -> +14155550171')
    print('Alternatively, enter a previous verification ID: ')
    phone = input('? ')

    if '+' in phone:
        verify_resp = hq_post('verifications', {'phone': phone, 'method': 'sms'})

        verification_id = verify_resp['verificationId']

        now = time()
        local_utc_offset = datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)
        exp_time = datetime.strptime(verify_resp['expires'], "%Y-%m-%dT%H:%M:%S.%fZ")
        exp_time += local_utc_offset

        print('Your verification ID is:')
        print(verification_id)
        print(f'Code expires at {exp_time.strftime("%Y-%m-%d %I:%M %p")}.')
    else:
        verification_id = phone

    print('Enter the code received via SMS: ')
    code = int(input('? '))

    auth_resp = hq_post(f'verifications/{verification_id}', {'code': code})

    print('Your bearer token is:')
    print(auth_resp['auth']['authToken'])


if __name__ == '__main__':
    main()
