"""Reproducible local measurements, using a temporary progress database."""
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import create_app
from engine.decision_engine import initial, advance
from engine.story_validator import validate
from stories.scenarios import SCENARIOS


def benchmark():
    paths=[(story,path) for story in SCENARIOS.values() for path in validate(story)]
    started=time.perf_counter();transitions=0
    for story,path in paths:
        snapshot=initial(story)
        for event in path['history']:
            snapshot=advance(story,snapshot,event['choice']);transitions+=1
    engine_seconds=time.perf_counter()-started
    with tempfile.TemporaryDirectory() as directory:
        started=time.perf_counter();app=create_app(Path(directory)/'benchmark.sqlite3',testing=True)
        startup=time.perf_counter()-started
        client=app.test_client();token=client.get('/api/bootstrap').json['csrf']
        def post(url,body):
            response=client.post(url,json=body,headers={'X-CSRF-Token':token})
            if response.status_code not in (200,201):raise RuntimeError(response.json)
            return response.json
        full_histories={}
        for story in SCENARIOS.values():
            path=validate(story)[0]
            journey=post('/api/journeys',{'scenario':story['id']})
            for event in path['history']:
                journey=post('/api/journeys/'+journey['id']+'/choose',{'scene':journey['snapshot']['scene'],'choice':event['choice'],'version':journey['version']})
            full_histories[journey['id']]=journey['snapshot']['history']
        timings=[]
        for _ in range(15):
            started=time.perf_counter();response=client.get('/api/bootstrap');timings.append(time.perf_counter()-started)
        compact=response.json
        compact_bytes=len(json.dumps(compact,separators=(',',':')).encode())
        for journey in compact['journeys']:journey['snapshot']['history']=full_histories[journey['id']]
        history_bytes=len(json.dumps(compact,separators=(',',':')).encode())
    result={'environment':sys.version.split()[0], 'routes':len(paths),'transitions':transitions,
        'engine_total_ms':round(engine_seconds*1000,2),'engine_mean_us_per_transition':round(engine_seconds/transitions*1e6,2),
        'cold_application_start_ms':round(startup*1000,2),'saved_journeys':len(SCENARIOS),
        'bootstrap_median_ms':round(statistics.median(timings)*1000,2),
        'bootstrap_max_ms':round(max(timings)*1000,2),'compact_bootstrap_bytes':compact_bytes,
        'equivalent_payload_with_histories_bytes':history_bytes,
        'payload_reduction_percent':round((1-compact_bytes/history_bytes)*100,1)}
    return result


if __name__=='__main__':
    result=benchmark()
    (ROOT/'docs/PERFORMANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
