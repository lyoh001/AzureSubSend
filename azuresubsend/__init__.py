import logging
import os

import azure.functions as func
import requests


def get_rest_api_token():
    oauth2_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    oauth2_body = {
        "client_id": os.environ["REST_CLIENT_ID"],
        "client_secret": os.environ["REST_CLIENT_SECRET"],
        "grant_type": "client_credentials",
        "resource": "https://management.azure.com",
    }
    oauth2_url = (
        f"https://login.microsoftonline.com/{os.environ['TENANT_ID']}/oauth2/token"
    )
    try:
        return requests.post(
            url=oauth2_url, headers=oauth2_headers, data=oauth2_body
        ).json()["access_token"]

    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def get_api_headers(token):
    return {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    }


def main(mytimer: func.TimerRequest) -> None:
    logging.info("******* Starting the function *******")
    rest_api_headers = get_api_headers(get_rest_api_token())
    try:
        url = f"https://management.azure.com/providers/Microsoft.Management/managementGroups/{(mg_id := min(mg['id'].split('/')[4] for mg in requests.get(url='https://management.azure.com/providers/Microsoft.Management/managementGroups?api-version=2020-02-01', headers=rest_api_headers).json()['value'] if 'Tenant Root Group' in mg['properties']['displayName']))}/descendants?api-version=2020-02-01"
        logging.info(
            requests.post(
                url=os.environ["LOGIC_APP_URL"],
                json={
                    "message": f"Found new subscription(s) in VICGOV root.\n{', '.join(subs)}\nPlease action the onboarding CICD pipeline to proceed or move it to 'Tenant Root Group/vicgovroot/Cenitex_Managed/Cancelled' to cancel."
                },
            )
            if (
                subs := [
                    sub["properties"]["displayName"]
                    for sub in requests.get(url=url, headers=rest_api_headers).json()[
                        "value"
                    ]
                    if all(
                        [
                            mg_id in sub["properties"]["parent"]["id"],
                            sub["properties"]["displayName"]
                            not in [
                                "Access to Azure Active Directory",
                                "vicgovroot",
                            ],
                        ]
                    )
                ]
            )
            else None,
        )
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
