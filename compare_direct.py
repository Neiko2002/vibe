import json

int8_data = json.load(open('results/yandex-200-cosine/deg_qg_summary_top100_int8.json'))
base_data = json.load(open('results/yandex-200-cosine/deg_qg_summary_top100.json'))

base_dict = {(d['config'], d.get('rerank_factor', 1.0), round(d['eps'], 4)): d for d in base_data}

print("=== Direct Comparison (K=16, LowLID, No-Prune, rerank=1.0x) ===")
print("eps    | Base Rec | INT8 Rec | Delta Rec | Base QPS | INT8 QPS | Delta QPS")
for d in int8_data:
    if d['k'] == 16 and d['opt_target'] == 'LowLID' and not d['prune_rng'] and d.get('rerank_factor') == 1.0:
        key = (d['config'], d.get('rerank_factor', 1.0), round(d['eps'], 4))
        if key in base_dict:
            b = base_dict[key]
            d_rec = (d['recall_100'] - b['recall_100']) * 100
            d_qps = (d['qps'] / b['qps'] - 1) * 100
            print(f"{d['eps']:6.3f} | {b['recall_100']*100:6.2f}% | {d['recall_100']*100:6.2f}% | {d_rec:+7.2f}% | {b['qps']:8.1f} | {d['qps']:8.1f} | {d_qps:+6.1f}%")

print("\n=== Direct Comparison (K=24, LowLID, No-Prune, rerank=1.0x) ===")
print("eps    | Base Rec | INT8 Rec | Delta Rec | Base QPS | INT8 QPS | Delta QPS")
for d in int8_data:
    if d['k'] == 24 and d['opt_target'] == 'LowLID' and not d['prune_rng'] and d.get('rerank_factor') == 1.0:
        key = (d['config'], d.get('rerank_factor', 1.0), round(d['eps'], 4))
        if key in base_dict:
            b = base_dict[key]
            d_rec = (d['recall_100'] - b['recall_100']) * 100
            d_qps = (d['qps'] / b['qps'] - 1) * 100
            print(f"{d['eps']:6.3f} | {b['recall_100']*100:6.2f}% | {d['recall_100']*100:6.2f}% | {d_rec:+7.2f}% | {b['qps']:8.1f} | {d['qps']:8.1f} | {d_qps:+6.1f}%")
