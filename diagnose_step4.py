import glob, os, json

files = sorted(glob.glob('evaluation/results/batch_*.jsonl'))
print('Result files found:', len(files))

if files:
    print('Latest:', files[-1])
    with open(files[-1]) as f:
        data = json.load(f)
    print('Keys:', list(data.keys()))
    print('Retrieval keys:', list(data.get('retrieval', {}).keys()) if data.get('retrieval') else 'EMPTY')
    
    if data.get('retrieval'):
        for agent, metrics in data['retrieval'].items():
            print(f'  {agent}: NDCG={metrics.get("ndcg")}, Hit@5={metrics.get("hit_at_5")}')
else:
    print('No batch eval result files found!')
