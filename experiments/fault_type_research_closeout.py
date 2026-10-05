"""唯讀盤點與研究收尾文件；規格見 docs/experiments/research_closeout.md。"""
import argparse
import gzip
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from core.logger import setup_run
from core.fault_type_final_guard import verify_seal

GROUPS = ['literature_expansion', 'mechanism_research_v2', 'continuous_research',
          'metric_classification_v1', 'local_fisher_v1', 'discriminative_prototypes_v1',
          'smooth_l1_v1', 'context_prototypes_v1', 'context_rejection_v1',
          'axis_invariant_kernel_v1', 'rpm_risk_extrapolation_v1']
FINGERPRINT = 'c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d'


def read(path):
    path = Path(path)
    with (gzip.open(path, 'rt', encoding='utf-8') if path.suffix == '.gz'
          else path.open(encoding='utf-8')) as stream:
        return json.load(stream)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def entries(value):
    """只列實體檔案的 SHA 對照，不把語意 seal 當檔案 SHA。"""
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield value
        else:
            for key, item in value.items():
                if key not in ['backup', 'archives', 'members']:
                    yield from entries(item)
    elif isinstance(value, list):
        for item in value:
            yield from entries(item)


def inspect_index(path):
    index = read(path)
    checked = []
    for item in entries(index):
        source = Path(item['path'])
        if source.suffix not in ['.json', '.gz', '.md', '.csv', '.txt']:
            continue
        if not source.is_file():
            checked.append(dict(path=str(source), status='INCOMPLETE', reason='來源檔不在現有位置'))
            continue
        actual = sha(source)
        if actual != item['sha256']:
            raise ValueError('索引 SHA 不符：' + str(source))
        checked.append(dict(path=str(source), sha256=actual, status='VERIFIED'))
    return dict(index=str(path), index_sha256=sha(path), checks=checked,
                archive_scope='沿已保存 whole／member SHA／CRC 驗收；本盤點不重新解包歷史 ZIP')


def summary_path(index):
    for key in ['summary', 'summary_compact']:
        if isinstance(index.get(key), str):
            return Path(index[key])
    if 'paths' in index:
        return Path(index['paths'].get('summary_compact', index['paths']['summary']))
    for item in index.get('compact_files', []):
        if Path(item['path']).name == 'summary.json.gz':
            return Path(item['path'])
    return Path(index['artifacts'].get('report_gzip', index['artifacts']['report'])['path'])


def protocol_path(index):
    if isinstance(index.get('protocol'), str):
        return Path(index['protocol'])
    if 'paths' in index:
        return Path(index['paths']['protocol'])
    for item in index.get('compact_files', []):
        if Path(item['path']).name == 'protocol.json':
            return Path(item['path'])
    return Path(index['artifacts']['protocol']['path'])


def numeric_methods(summary):
    """保留原分母與全部 seed；不重新計算分類、誤報或選 winner。"""
    methods = summary['methods']
    if isinstance(methods, list):
        result = {}
        for item in methods:
            key = str(item.get('method_id', item.get('arm_id'))) + '/' + str(item.get('score_id', ''))
            if key in result:
                raise ValueError('重複方法 ID：' + key)
            result[key] = item
        return result
    return methods


def check_summary(path):
    data = read(path)
    key = next((k for k in ['report_checksum', 'summary_checksum'] if k in data), None)
    if key is None:
        raise ValueError('報告沒有語意 seal：' + str(path))
    verify_seal(data, key)
    return data, key


def stage_paths(index):
    result = {}
    aliases = {'locked':'fit', 'fit_lock':'fit', 'lock':'fit', 'source_verification':'source_proof',
               'evaluation':'evaluate', 'verified':'verify', 'verification':'verify',
               'summary':'report', 'report':'report', 'archive_verification':'backup'}
    for mapping in [index, index.get('paths', {}), index.get('artifacts', {})]:
        for key, stage in aliases.items():
            item = mapping.get(key)
            if isinstance(item, str): result[stage] = item
            elif isinstance(item, dict) and 'path' in item: result[stage] = item['path']
    for item in index.get('compact_files', []):
        name = Path(item['path']).name
        stage = {'locked_study.json':'fit','source_verified.json':'source_proof',
                 'evaluation.json.gz':'evaluate','verified.json.gz':'verify',
                 'summary.json.gz':'report'}.get(name)
        if stage: result[stage] = item['path']
    output = {}
    for stage, path in result.items():
        source = Path(path)
        if not source.is_file():
            output[stage] = dict(path=path, status='INCOMPLETE')
            continue
        data = read(source)
        keys = [key for key in ['locked_checksum','source_verification_checksum','evaluation_checksum',
                               'verification_checksum','report_checksum','summary_checksum'] if key in data]
        # 只驗本物件的 seal；引用父物件的 seal 不是此物件的 digest。
        own = {'fit':'locked_checksum','source_proof':'source_verification_checksum','evaluate':'evaluation_checksum',
               'verify':'verification_checksum','report':'report_checksum'}.get(stage)
        if own not in keys and stage == 'report' and 'summary_checksum' in keys: own='summary_checksum'
        if own in keys: verify_seal(data, own)
        output[stage] = dict(path=path, sha256=sha(source),
                             status='VERIFIED_SEAL' if own in keys else 'SAVED_EVIDENCE_SHA_RECORDED',
                             semantic_key=own if own in keys else None,
                             semantic_seal=data[own] if own in keys else None)
    return output


def decision(summary):
    gates = summary['reliability']
    passed = [name for name, gate in gates.items() if gate['main_screen'] == 'PASS']
    if any(gate['main_screen'] not in ['PASS', 'FAILED', 'INCOMPLETE'] for gate in gates.values()):
        raise ValueError('未知主篩狀態')
    return dict(path='A' if passed else 'B', candidates_for_limited_confirmation=passed,
                reliable_improvement_reached=False,
                completed_runs=summary['completed_runs'], paired_comparisons=len(summary['paired_differences']),
                full_contract_gates=gates,
                independent_final_guard='INCOMPLETE', raw_acquisition_independence='UNKNOWN',
                historical_test_exposure=True,
                group_dro='已規劃未實作，本階段收尾，未進入訓練或測試',
                conclusion='存在主篩候選，尚須有限確認' if passed else '尚未找到通過契約的方法，本研究階段收尾')


def run(pools, *, m_report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    inventory = []
    catalog = {}
    for group in pools:
        path = Path('reports') / group / 'result_index.json'
        checked = inspect_index(path)
        index = read(path)
        summary_file = summary_path(index)
        report, key = check_summary(summary_file)
        protocol_file = protocol_path(index)
        protocol = read(protocol_file)
        verify_seal(protocol, 'protocol_checksum')
        if protocol['protocol_checksum'] != report['protocol_checksum']:
            raise ValueError('報告與協定不相符：' + group)
        checked.update(summary=str(summary_file), summary_sha256=sha(summary_file),
                       semantic_key=key, semantic_seal=report[key],
                       completed=report.get('completed_runs', report.get('completed_evaluations')),
                       prediction_records=report.get('prediction_records'),
                       unique_samples=report.get('unique_samples', report.get('unique_test_rows')),
                       protocol=str(protocol_file), protocol_sha256=sha(protocol_file),
                       protocol_checksum=protocol['protocol_checksum'],
                       stages=stage_paths(index),
                       stage_evidence={k:v for k,v in index.items() if k in
                           ['paths','counts','archive_verification','archive_indices','tests','phase_commits',
                            'protocol_commit','source_commit','new_classifier_fits','successful_training_models']})
        inventory.append(checked)
        catalog[group] = dict(summary=str(summary_file), summary_sha256=sha(summary_file),
                              methods=numeric_methods(report), protocol=protocol,
                              source_documents=[str(p) for p in (Path('reports') / group).glob('*source*.md')],
                              report_path=str(Path('reports') / group / 'final_findings.md'),
                              reliability=report.get('reliability', {}),
                              counts={k:v for k,v in report.items() if k not in
                                      ['methods','paired_differences','reliability'] and not isinstance(v,(dict,list))})
    report, key = check_summary(m_report)
    inventory.append(dict(batch='feature_self_challenging_v1', summary=str(m_report),
                          summary_sha256=sha(m_report), semantic_seal=report[key],
                          completed=report['completed_runs'], prediction_records=report['prediction_records'],
                          unique_samples=report['unique_samples']))
    mp = read('output/fault_type_self_challenging_lock/2026-10-04-22-01-49/protocol.json')
    verify_seal(mp, 'protocol_checksum')
    if mp['protocol_checksum'] != report['protocol_checksum']:
        raise ValueError('M 報告與協定不相符')
    catalog['feature_self_challenging_v1'] = dict(summary=str(m_report), summary_sha256=sha(m_report),
                                                methods=numeric_methods(report), protocol=mp,
                                                source_documents=['reports/feature_self_challenging_v1/sources.md'],
                                                reliability=report['reliability'],
                                                counts={k:v for k,v in report.items() if k not in
                                                        ['methods','paired_differences','reliability'] and not isinstance(v,(dict,list))})
    # 只重算既有 manifest 的支持筆數，不讀取特徵、不 fit。
    from experiments.fault_type_discriminative_prototypes import check
    from core.fault_type_accuracy_pipeline import records_for
    _, _, manifests, _, _ = check(catalog['discriminative_prototypes_v1']['protocol'])
    support = []
    for fold, manifest in enumerate(manifests):
        roles = {}
        for role in ['train', 'calibration', 'test']:
            rows = records_for(manifest, role)
            ids = sorted(row['sample_id'] for row in rows)
            roles[role] = dict(samples=len(rows), classes=dict(Counter(row['label'] for row in rows)),
                               rpms=dict(Counter(row['rpm'] for row in rows)),
                               sample_ids_sha256=hashlib.sha256(json.dumps(ids, ensure_ascii=False).encode('utf-8')).hexdigest())
        support.append(dict(fold=fold, manifest_checksum=mp['manifest_checksums'][fold], roles=roles))
    result = dict(date='2026-10-05', timezone='Asia/Taipei',
                  head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  dataset_fingerprint=FINGERPRINT, fingerprint_scope='已封存來源核驗；本盤點不重新載入 data',
                  batches=inventory, retraining=False, old_full_tests_rerun=False,
                  historical_exposure=True, new_independent_data=False)
    for name, data in [('checkpoint_inventory', result), ('method_catalog', catalog),
                       ('decision_record', decision(report))]:
        (output / (name + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'fold_support.json').write_text(json.dumps(support, ensure_ascii=False, indent=2), encoding='utf-8')
    with gzip.open(output / 'method_catalog.json.gz', 'wt', encoding='utf-8') as stream:
        json.dump(catalog, stream, ensure_ascii=False, separators=(',', ':'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--m-report', type=Path, required=True)
    parser.add_argument('--document-runtime', type=Path)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--word', action='store_true')
    parser.add_argument('--renderer', type=Path)
    args = parser.parse_args()
    log, paths = setup_run('fault_type_research_closeout')
    if args.document_runtime:
        if not args.inventory:
            parser.error('文件編排需要 --inventory')
        command = [str(args.document_runtime), 'reports/research_closeout_20261005/build_report.py',
                   '--inventory', str(args.inventory), '--output', str(paths.output_dir)]
        if args.word: command.append('--word')
        if args.renderer: command += ['--renderer', str(args.renderer)]
        completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        log.info('文件編排 stdout：{}', completed.stdout.rstrip())
        if completed.returncode:
            log.error('文件編排 stderr：{}', completed.stderr)
            raise RuntimeError('文件編排未完成')
        return
    result = run(GROUPS, m_report=args.m_report, output=paths.output_dir)
    log.info('盤點完成 {} 批，沒有新增訓練；輸出 {}', len(result['batches']), paths.output_dir)


if __name__ == '__main__':
    main()
