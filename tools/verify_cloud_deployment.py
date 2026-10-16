"""Read-only live checks. Never signs up users or prints credentials."""
import json
from pathlib import Path
import requests
from victor.deployment import deployment

def main():
    root=Path(__file__).resolve().parents[1]
    config=deployment(root)['cloud']
    headers={'apikey':config['publishable_key']}
    report={'project':'igqveyxbwhnadyubtsnj','checks':{}}
    with requests.Session() as http:
        for name,path in [('auth_settings','/auth/v1/settings'),('anonymous_profiles','/rest/v1/profiles?select=id'),('anonymous_events','/rest/v1/login_events?select=id')]:
            response=http.get(config['url']+path,headers=headers,timeout=(5,15),allow_redirects=False)
            if name=='auth_settings':
                response.raise_for_status()
                settings=response.json()
                report['checks'][name]={'status':response.status_code,'email_enabled':settings.get('external',{}).get('email'),'email_autoconfirm':settings.get('mailer_autoconfirm')}
                assert settings.get('external',{}).get('email') is True
                assert settings.get('mailer_autoconfirm') is False
            else:
                report['checks'][name]={'status':response.status_code,'denied':response.status_code in (401,403)}
                assert response.status_code in (401,403), name+' is exposed'
    (root/'docs/cloud_live_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
