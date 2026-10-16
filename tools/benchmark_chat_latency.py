"""Two public prompts on the configured ChatGPT account; never logs tokens or credentials."""
import json
from pathlib import Path
import threading
import time
from victor.config import ConfigManager
from victor.ai.manager import AIManager

def main():
    root=Path(__file__).resolve().parents[1];config=ConfigManager(root);cfg=config.snapshot();report={'measurements':[]}
    manager=AIManager(config,lambda *args:None)
    try:
        if cfg['provider']!='OpenAI' or cfg['auth_methods']['OpenAI']!='account':
            report['status']='skipped';report['reason']='La configuración activa no usa cuenta ChatGPT. No se cambió proveedor ni método de pago.'
        else:
            for attempt in range(2):
                start=time.perf_counter();first=[]
                def token(value):
                    if not first:first.append(time.perf_counter()-start)
                reply=manager.generate([{'role':'user','content':'Responde solo con: Hola.'}],'Responde en español con brevedad.',[],threading.Event(),on_token=token)
                report['measurements'].append({'attempt':attempt,'first_text_seconds':first[0] if first else None,'total_seconds':time.perf_counter()-start,'answer_chars':len(reply.text)})
            report['status']='completed'
    except Exception as exc:
        report['status']='failed';report['error_type']=type(exc).__name__
    finally:manager.close()
    output=root/'docs/chat_latency.json';baseline=root/'docs/chat_latency_baseline.json'
    if output.exists() and not baseline.exists():baseline.write_bytes(output.read_bytes())
    report['reasoning_effort']=cfg.get('ai_reasoning_effort','low')
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
