import requests

API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
API_KEY = 'ZjgwZTFlNzUtZmI2Mi00NDI5LTgwNGUtOWQ5MmMxNzQ1OWQxOmM4ODgwYTQ2LTRkNjUtNDNkMi05YzExLTJmNGM3MWRiYzE4Yg=='


def get_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload = 'scope=GIGACHAT_API_PERS'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': '6f0b1291-c7f3-43c6-bb2e-2f3efb3dc98e',
        'Authorization': f'Basic {API_KEY}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)

    return response.json()['access_token']


def get_answer(prompt, text):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {get_token()}'
    }
    data = {
        "model": 'GigaChat',
        "messages": [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "n": 1,
        "stream": False,
        "max_tokens": 2048,
        "repetition_penalty": 1,
        "update_interval": 0
    }

    response = requests.post(API_URL, headers=headers, json=data, verify=False)
    try:
        answer = response.json()['choices'][0]['message']['content']
        return answer
    except Exception:
        return None



