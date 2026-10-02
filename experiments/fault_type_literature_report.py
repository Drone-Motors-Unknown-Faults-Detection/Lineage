"""All-method markdown and compact indices; descriptive bests, never deployment."""
from __future__ import annotations
import argparse
import json
import gzip
from pathlib import Path
import numpy as np
from core.fault_type_final_guard import seal,verify_seal
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_accuracy_report import METRICS
from experiments.fault_type_accuracy_summary import pareto


def value(m,k):return m['equal_motor_descriptive'].get(k,{}).get('mean')
def pct(v):return 'NA' if v is None else f'{100*v:.2f}'
def metric(m,k):return value(m,k)
def read(p):return json.loads(gzip.decompress(p.read_bytes())) if p.suffix=='.gz' else json.loads(p.read_text(encoding='utf-8'))


def historical_comparison(current, historic, new, old, score):
    differences={k:value(current,k)-value(historic,k) for k in METRICS
                 if value(current,k) is not None and value(historic,k) is not None}
    classification={k:d for k,d in differences.items()
                    if k.startswith('known_classification.') or k.startswith('known_fault_classification.')}
    return {'new':new+'/'+score, 'historical':old+'/'+score, 'mean_differences':differences,
            'matches':bool(differences) and all(abs(d)<1e-12 for d in differences.values()),
            'classification_matches':bool(classification) and all(abs(d)<1e-12 for d in classification.values()),
            'expected_entire_method_match':True,
            'reference_scope_note':'C02 and A0 both mixed-RPM references' if new=='C02' else
                'C24 separately fits/calibrates RPM references; historical A7 shared the per-RPM A1 '
                'reference (A1 rpm_strategy=separate). Classifier and detector scopes are both identical; '
                'sharing a fitted reference does not mean pooling RPMs. Full metrics should reproduce.',
            'scope':'saved historical summaries; not refit historical study'}


def run(pools,*,protocol,lock,verified,prior,output,inputs):
    for data,key in [(protocol,'protocol_checksum'),(lock,'locked_checksum'),(verified,'report_checksum'),(prior,'summary_checksum')]:verify_seal(data,key)
    if verified['protocol_checksum']!=protocol['protocol_checksum'] or verified['locked_checksum']!=lock['locked_checksum']:raise ValueError('report binding')
    from experiments.fault_type_literature_registry import check
    from experiments.fault_type_literature_study import validate_lock,load_bundle
    manifests=check(protocol);audits=validate_lock(lock,protocol,manifests)
    methods=verified['methods'];mapping={m['arm_id']+'/'+m['score_id']:m for m in methods};checks=[]
    for new,old in [('C02','A0'),('C24','A7')]:
        for score in ['mahalanobis','knn']:
            current=mapping[new+'/'+score];historic=next(m for m in prior['methods'] if (m['arm_id'],m['score_id'])==(old,score))
            checks.append(historical_comparison(current,historic,new,old,score))
    keys=['known_fault_classification.accuracy','known_fault_classification.balanced_accuracy','known_classification.accuracy',
        'unknown_rejection.auroc_unknown_positive','unknown_rejection.unknown_recall','final_open_set_classification.accuracy']
    descriptive=[]
    for k in keys:
        complete=[m for m in methods if len([s for mot in m['motor_results'] for s in mot['seed_results']])==9 and value(m,k) is not None]
        ordered=sorted(complete,key=lambda m:(-value(m,k),m['arm_id'],m['score_id']))
        descriptive.append({'metric':k,'scope':'POSTHOC_DESCRIPTIVE_SEARCH_MAXIMUM_NOT_VALIDATED_SELECTION','top5':[{'method':m['arm_id']+'/'+m['score_id'],
            'value':value(m,k),'healthy_fpr':value(m,'healthy_safety.false_positive_rate'),'known_rejection':value(m,'known_rejection_rate')} for m in ordered[:5]]})
    warning_rows=[];optimizer_rows=[]
    for a in lock['artifacts']:
        if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('report model SHA changed')
        bundle=load_bundle(a,lock,protocol,manifests,audits)
        warning_rows.extend(dict(w,fold_id=a['fold_id'],seed=a['seed']) for w in bundle['warnings'])
        optimizer_rows.extend({'fold_id':a['fold_id'],'seed':a['seed'],'reference':name,'optimizer':ref['transformer'].optimizer,
            'fit_subset_count':len(ref['transformer'].metric_subset_indices)} for name,ref in bundle['references'].items() if ref['transformer'].optimizer)
    result=seal({'scope':protocol['scope'],'protocol_checksum':protocol['protocol_checksum'],'locked_checksum':lock['locked_checksum'],
        'verified_checksum':verified['report_checksum'],'inputs':inputs,'planned_evaluations':630,'completed_evaluations':verified['completed_runs'],
        'failed_evaluations':verified['failed_runs'],'prediction_records':verified['prediction_records'],'unique_test_rows':verified['unique_test_rows'],
        'methods':methods,'historical_control_checks':checks,'descriptive_metric_maxima':descriptive,'descriptive_pareto':pareto(methods),
        'paired_differences':verified['paired_differences'],'fit_counts':lock['fit_counts'],'physical_bundle_fit_seconds':sum(a['seconds'] for a in lock['artifacts']),
        'warnings':warning_rows,'nca_optimizer':optimizer_rows,'selection_policy':'none','fresh_final_test':False,'independent_validation':'INCOMPLETE',
        'defaults_modified':False},'summary_checksum')
    save_json(output/'summary.json',result);(output/'summary.json.gz').write_bytes(gzip.compress(json.dumps(result,sort_keys=True,allow_nan=False).encode(),mtime=0))
    lines=['# 文獻導向擴展與改編實測（2026-10-02）','',
        f"實際完成 {result['completed_evaluations']}/630 組，未完成 {len(result['failed_evaluations'])} 組；{result['prediction_records']:,} 筆逐樣本預測（同28,910個樣本重複使用，不是新的獨立資料）。",
        '', '只有現有三顆不同馬達資料；healthy＋5 known螺絲配置／4 unknown螺絲配置，不是9種確認物理故障原因。全部樣本歷史已曝光，本輪前鎖定不能消除曝光。以下最高分是多方法搜尋的描述性結果，不能直接宣稱可靠或部署winner。',
        '', '## 全部分類方法', '', '| ID | 表示法／RPM／分類器／變更係數 | fault-only accuracy% | fault-only BA% | fault-only macro-F1% | healthy+known accuracy% |', '|---|---|---:|---:|---:|---:|']
    for a in protocol['arms']:
        m=mapping.get(a['id']+'/mahalanobis')
        values=[value(m,k) if m else None for k in ['known_fault_classification.accuracy','known_fault_classification.balanced_accuracy','known_fault_classification.macro_f1','known_classification.accuracy']]
        lines.append(f"| {a['id']} | {a['representation']} / {a['rpm_strategy']} / {a['classifier']} / {a['parameter']} | "+' | '.join(pct(v) for v in values)+' |')
    lines+=['','兩factory共用分類器：closed-set accuracy相同是正常；拒絕後final分類另列，不混用同名accuracy。','','## 全部開集方法', '',
        '| 方法 | AUROC | unknown recall% | healthy FPR% | known rejection% | final open-set accuracy% |', '|---|---:|---:|---:|---:|---:|']
    for m in methods:
        values=[value(m,k) for k in ['unknown_rejection.auroc_unknown_positive','unknown_rejection.unknown_recall','healthy_safety.false_positive_rate','known_rejection_rate','final_open_set_classification.accuracy']]
        lines.append('| '+m['arm_id']+'/'+m['score_id']+' | '+('NA' if values[0] is None else f'{values[0]:.4f}')+' | '+' | '.join(pct(v) for v in values[1:])+' |')
    lines+=['','## 描述性最高分（不是部署選擇）','']
    for d in descriptive:
        lines.append(f"- {d['metric']}: "+'; '.join(f"{m['method']}={m['value']:.6f}, healthy FPR={m['healthy_fpr']:.6f}, known rejection={m['known_rejection']:.6f}" for m in d['top5'][:3]))
    lines+=['','## 逐馬達與轉速完整證據','','所有方法、3seed實值、3motor、RPM、配置逐類召回與confusion matrices見compact summary及verified.json.gz，均由保存預測重算並與sealed模型重新推論逐筆比對。以下每方法三顆馬達均值，不挑最好seed。','',
        '| 方法 | test motor | fault-only accuracy% | unknown AUROC | unknown recall% | healthy FPR% |', '|---|---|---:|---:|---:|---:|']
    for m in methods:
        for motor in m['motor_results']:
            v=motor['values'];get=lambda k:v.get(k,{}).get('mean')
            auc=get('unknown_rejection.auroc_unknown_positive')
            lines.append(f"| {m['arm_id']}/{m['score_id']} | {motor['motor']} | {pct(get('known_fault_classification.accuracy'))} | "+('NA' if auc is None else f'{auc:.4f}')+f" | {pct(get('unknown_rejection.unknown_recall'))} | {pct(get('healthy_safety.false_positive_rate'))} |")
    lines+=['','## 工程狀態與未通過項目','',
        '- 用途分離：各fold train/cal/test不同motor；無global selector，validation/selection IDs空。只有known train做scaler/PCA/NCA/classifier/reference，known cal只校準固定score；其他開發motor unknown unused。',
        '- source fingerprint與90CSV SHA前後未變；factory Maha-LW/kNN基礎、正式105維資料與PolarMap未改；已封存歷史檔案不覆寫。',
        '- 未通過方法不能以借test/cal fit、填補missing predicted group或翻轉符號來救分數；全部未完成格與reason列summary。',
        '- NCA固定50iteration預算；觸頂者屬近似／budget-limited，不宣稱已找到最优嵌入。其他warnings完整列summary。',
        '- 老師healthy＋5known／4unknown與按motor群組切分：本輪實際執行主固定配置。其他N／全部126組本輪未重跑，歷史2490次只讀。',
        '- 每fold僅1個test motor，guard每類至少2 test groups要求仍INCOMPLETE；來源session、raw overlap、IQR mask與物理一致性仍UNKNOWN。不能將seeds、RPM、windows當作獨立馬達；無IID窗CI、無RUL、無量化老化。',
        '- 無新的fresh final test，模型選擇／可靠部署未驗證；健康FPR零只是此資料觀察，不是固定5%保證。',
        '', '## 原始來源與改編定位', '', '28項封存來源加3項補充來源，共31項書目；見repository的reports/literature_expansion/sources.md與sources_addendum.md。部分只作範圍依據，不是31套新演算法已實測。C/R ID參數逐項見封存protocol。自訂表示法、RDA-inspired混合、RMD係數、預測類別cal、融合在core/fault_type_literature.py有函數級來源；不是聲稱新原創已發表方法。',
        '', '## 歷史控制與成本','',f"{json.dumps(checks,ensure_ascii=False)}",'',
        'C02/A0檢查完整混合RPM方法；C24/A7檢查完整RPM分開方法。舊registry的A1 rpm_strategy=separate，A7共用的是per-RPM reference，不是mixed-RPM。四組控制的實際matches及全部差異見上列；未改已鎖定本輪方法來追求歷史分數一致。','',
        f"physical bundle fit seconds={result['physical_bundle_fit_seconds']:.3f}; fit counts={result['fit_counts']}. 各邏輯run共享模型／參照，不把630組當630個獨立訓練或受試馬達。"]
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['protocol','locked','verified','prior']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();log,paths=setup_run('fault_type_literature_report')
    inputs={k:{'path':str(getattr(a,k).resolve()),'sha256':_sha256_file(getattr(a,k))} for k in ['protocol','locked','verified','prior']}
    result=run(None,protocol=read(a.protocol),lock=read(a.locked),verified=read(a.verified),prior=read(a.prior),output=paths.output_dir,inputs=inputs)
    log.info('report {} methods; no selector; output={}',len(result['methods']),paths.output_dir)


if __name__=='__main__':main()
