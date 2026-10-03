"""實驗17：固定RPM工況原型；未知不擬合，正式預設不變。"""
import argparse
import gzip
import json
import platform
import shutil
import subprocess
import time
from pathlib import Path
import joblib
import numpy as np
import sklearn
from loguru import logger
from threadpoolctl import threadpool_limits
from core.fault_type_context_prototypes import ContextPrototypes, RPMS, AUXILIARY
from core.fault_type_discriminative_prototypes import OPTIONS, BETA, EPSILON
from core.fault_type_metric_classifiers import weight_transform
from core.fault_type_accuracy_pipeline import records_for, check_cell
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal, verify_seal, digest
from core.fault_type_provenance import save_json
from core.fault_type_metrics_v2 import decision, classification
from core.fault_type_reliability import CONTRACT, assess
from core.fault_type_mechanisms import peak_memory_bytes
from core.formal_data import _sha256_file
from core.logger import setup_run
from experiments import fault_type_discriminative_prototypes as G
from experiments.fault_type_smooth_l1 import validate_parent_source, parent_bundle
from experiments.fault_type_fixed_calibration import verify_sources
from experiments.fault_type_literature_study import artifact, write_gzip, read_gzip, make_rows
from experiments.fault_type_mechanism_study import summarized, check_rows, save_immutable
from experiments.fault_type_mechanism_report import predictions, summarize

MODELS = [dict(id=f'{g}_{d}_{v}', geometry=g, degree=d, variant=v)
          for g in ['identity', 'metric'] for d in [1, 2] for v in ['static', 'glvq', 'auxiliary']]
ARMS = [dict(id=f'I{i+1:02}', model=m['id'], detector='C02/M') for i, m in enumerate(MODELS)]
PARAMETERS = dict(models=MODELS, optimizer=OPTIONS, beta=BETA, epsilon=EPSILON, auxiliary=[0., AUXILIARY],
                  context_rpms=list(RPMS), context='(RPM-8000)/3000', prototype_seconds=120,
                  initialization='all known train class least squares', loss_subset_per_class_rpm=20)
BUDGET = dict(planned_runs=108, seconds_per_action=1800, reserve_C_bytes=1000000000)
FILES = ['core/fault_type_context_prototypes.py', 'experiments/fault_type_context_prototypes.py',
         'docs/experiments/exp17_context_prototypes.md', 'experiments/fault_type_smooth_l1.py']
KEYS = ['dataset_fingerprint', 'known_labels', 'unknown_labels', 'rpms', 'folds', 'seeds', 'factory_parameters',
        'exposure_ledger_checksum', 'manifest_checksums', 'reliability_contract', 'parent_protocol_checksum']
BASE = Path('D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/context_prototypes_v1/workspace/output')
read = G.read


def build(protocol, lock, source):
    gp, gl, gs = read(protocol), read(lock), read(source)
    G.check(gp)
    validate_parent_source(gp, gl, gs)
    p = {k: gp[k] for k in KEYS}
    p.update(version='exp17_context_prototypes_v1', parent_protocol=artifact(protocol), parent_lock=artifact(lock),
             parent_source=artifact(source), parameters=PARAMETERS, arms=ARMS, budget=BUDGET,
             environment={'python': platform.python_version(), 'sklearn': sklearn.__version__},
             implementations=[artifact(Path(f)) for f in FILES], selection_policy='none', selection_sample_ids=[],
             validation_sample_ids=[], shared_validation_calibration=False, fresh_final_test=False,
             scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED', source_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
    return seal(p, 'protocol_checksum')


def validate_policy(p):
    if (p['selection_policy'] != 'none' or p['selection_sample_ids'] or p['validation_sample_ids'] or
            p['shared_validation_calibration'] or p['fresh_final_test'] or
            any(k in p for k in ['global_winner', 'selected_representation', 'selected_model']) or
            p['scope'] != 'EXPLORATORY_HISTORICAL_TEST_EXPOSED'):
        raise ValueError('context selection/exposure policy')


def check(p):
    verify_seal(p, 'protocol_checksum')
    validate_policy(p)
    if (p['version'] != 'exp17_context_prototypes_v1' or p['parameters'] != PARAMETERS or p['arms'] != ARMS or
            p['budget'] != BUDGET or p['reliability_contract'] != CONTRACT or p['selection_policy'] != 'none' or
            p['selection_sample_ids'] or p['validation_sample_ids'] or p['shared_validation_calibration'] or p['fresh_final_test']):
        raise ValueError('fixed context protocol changed')
    if p['environment'] != {'python': platform.python_version(), 'sklearn': sklearn.__version__}:
        raise ValueError('native context environment required')
    if [a['path'] for a in p['implementations']] != [str(Path(f).resolve()) for f in FILES]:
        raise ValueError('source inventory')
    for a in p['implementations']+[p['parent_protocol'], p['parent_lock'], p['parent_source']]:
        if _sha256_file(Path(a['path'])) != a['sha256']:
            raise ValueError('context source SHA')
    gp, gl, gs = [read(p[k]['path']) for k in ['parent_protocol', 'parent_lock', 'parent_source']]
    ep, pp, ms, old, audits = G.check(gp)
    validate_parent_source(gp, gl, gs)
    if any(p[k] != gp[k] for k in KEYS):
        raise ValueError('parent context protocol binding')
    return gp, ep, pp, ms, old, audits, gl


def rpm_values(records):
    values = []
    for r in records:
        code = r['rpm']
        if code not in ['6000rpm', '8000rpm', '11000rpm']:
            raise ValueError('documented RPM metadata required')
        values.append(int(code[:-3]))
    return np.asarray(values, int)


def expected_audits(p, m, parent, ix):
    tr, ca = records_for(m, 'train'), records_for(m, 'calibration')
    check_cell(tr, ca, p['known_labels'])
    ids, cis = [r['sample_id'] for r in tr], [r['sample_id'] for r in ca]
    if set(ids)&set(cis) or set(ids+cis)&set(m['sample_ids']['test']) or len(set(m['motor_roles'].values())) != 3:
        raise ValueError('context motor/sample purpose overlap')
    sub = [ids[i] for i in ix]
    return [dict(definition=a, protocol_checksum=p['protocol_checksum'], manifest_checksum=m['manifest_checksum'],
                 dataset_fingerprint=p['dataset_fingerprint'], seed=parent['seed'], motor_roles=m['motor_roles'],
                 scaler_fit_ids=ids, representation_fit_ids=ids, classifier_initialization_ids=ids, classifier_fit_ids=ids,
                 prototype_loss_fit_ids=[] if d['variant'] == 'static' else sub,
                 metric_fit_ids=sub if d['geometry'] == 'metric' else [], reference_fit_ids=ids,
                 calibration_sample_ids=cis, selection_sample_ids=[], selection_policy='none', shared_validation_calibration=False,
                 context_fit_ids=ids, train_rpm_checksum=digest(rpm_values(tr).tolist()),
                 calibration_rpm_checksum=digest(rpm_values(ca).tolist()), inference_inputs=['features', 'documented RPM'],
                 detector_source='parent C02/M factory; no new calibration choice') for d, a in zip(MODELS, ARMS)]


def fit_node(d, Z, C, y, rpm, cal_rpm, ix, seed):
    model = ContextPrototypes(d['degree'], d['variant'], seed).fit(Z, y, rpm, ix, seconds=120)
    active = model.optimizer_['success']
    return dict(model=model, status='completed' if active else 'INCOMPLETE',
                train_array_checksum=digest(Z.tolist()), calibration_array_checksum=digest(C.tolist()),
                train_rpm_checksum=digest(np.asarray(rpm).tolist()), calibration_rpm_checksum=digest(np.asarray(cal_rpm).tolist()),
                train_predictions_checksum=digest(model.predict(Z, rpm).tolist()) if active else None)


def verify_node(node, d, Z, C, y, rpm, cal_rpm, ix, seed):
    expected = fit_node(d, Z, C, y, rpm, cal_rpm, ix, seed)
    if (node['model'].signature() != node['model'].checksum_ or node['model'].checksum_ != expected['model'].checksum_ or
            any(node[k] != expected[k] for k in expected if k != 'model')):
        raise ValueError('actual context train/cal/RPM source mismatch')
    return dict(status=expected['status'], state_checksum=expected['model'].checksum_, optimizer=expected['model'].optimizer_)


def budget(start):
    if time.perf_counter()-start > BUDGET['seconds_per_action'] or shutil.disk_usage('C:/').free < BUDGET['reserve_C_bytes']:
        raise RuntimeError('context budget; preserve checkpoints')


def source_arrays(pools, parent, p, m, weights):
    y, spaces = G.source_arrays(pools, parent, p, m, weights)
    return y, spaces, rpm_values(records_for(m, 'train')), rpm_values(records_for(m, 'calibration'))


def load_model(a, p, m, context):
    for f in [a, a['fit_audits']]:
        if _sha256_file(Path(f['path'])) != f['sha256']:
            raise ValueError('context model/audit SHA')
    b = joblib.load(a['path'])
    ga, parent, weights, ix = parent_bundle(p, m, a['seed'], context)
    if (b['protocol_checksum'] != p['protocol_checksum'] or b['manifest_checksum'] != m['manifest_checksum'] or
            b['seed'] != a['seed'] or b['parent_sha256'] != ga['sha256'] or a['parent_artifact'] != ga or b['weights'] != weights or
            b['audits'] != expected_audits(p, m, ga, ix) or read_gzip(a['fit_audits']['path']) != b['audits'] or
            set(b['nodes']) != {d['id'] for d in MODELS}):
        raise ValueError('context model/source binding')
    for d in MODELS:
        node = b['nodes'][d['id']]
        model = node['model']
        if (model.degree != d['degree'] or model.variant != d['variant'] or model.seed != a['seed'] or
                model.signature() != model.checksum_ or model.options_ != OPTIONS or
                (node['status'] == 'completed') != model.optimizer_['success']):
            raise ValueError('context definition/state/status')
    return b, parent, ix


def fit(pools, p, output):
    context = check(p)
    ms, gl = context[3], context[6]
    before = verify_sources(pools.root, ms[0])
    start, arts = time.perf_counter(), []
    with threadpool_limits(limits=1):
        for ga in gl['artifacts']:
            budget(start)
            m = next(x for x in ms if x['fold_id'] == ga['fold_id'])
            cell = output/(m['fold_id']+'_seed'+str(ga['seed']))
            cell.mkdir(exist_ok=True)
            cp = cell/'checkpoint.json'
            if cp.exists():
                saved = read(cp)
                verify_seal(saved, 'checkpoint_checksum')
                load_model(saved['artifact'], p, m, context)
                arts.append(saved['artifact'])
                continue
            t = time.perf_counter()
            _, parent, weights, ix = parent_bundle(p, m, ga['seed'], context)
            y, spaces, rpm, cr = source_arrays(pools, parent, p, m, weights)
            nodes = {d['id']: fit_node(d, *spaces[d['geometry']], y, rpm, cr, ix, ga['seed']) for d in MODELS}
            b = dict(protocol_checksum=p['protocol_checksum'], manifest_checksum=m['manifest_checksum'], seed=ga['seed'],
                     parent_sha256=ga['sha256'], weights=weights, nodes=nodes, audits=expected_audits(p, m, ga, ix))
            joblib.dump(b, cell/'model.joblib', compress=3)
            write_gzip(cell/'fit_audits.json.gz', b['audits'])
            a = dict(artifact(cell/'model.joblib'), fold_id=m['fold_id'], seed=ga['seed'], parent_artifact=ga,
                     fit_audits=artifact(cell/'fit_audits.json.gz'), seconds=time.perf_counter()-t, process_peak_memory_bytes=peak_memory_bytes())
            load_model(a, p, m, context)
            save_json(cp, seal(dict(artifact=a, protocol_checksum=p['protocol_checksum']), 'checkpoint_checksum'))
            arts.append(a)
            logger.info('封存 {}，成功{}模型', cell.name, sum(n['status'] == 'completed' for n in nodes.values()))
    after = verify_sources(pools.root, ms[0])
    if before != after:
        raise ValueError('formal data changed')
    return save_immutable(output/'locked_study.json', seal(dict(protocol_checksum=p['protocol_checksum'], artifacts=arts,
        source_before=before, source_after=after, environment=p['environment'], selection_policy='none', selection_sample_ids=[],
        code_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()), 'locked_checksum'), 'locked_checksum')


def source_verify(pools, p, lock, output):
    context = check(p)
    G.validate_lock(p, lock)
    start, cells = time.perf_counter(), []
    before = verify_sources(pools.root, context[3][0])
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start)
            m = next(x for x in context[3] if x['fold_id'] == a['fold_id'])
            b, parent, ix = load_model(a, p, m, context)
            y, spaces, rpm, cr = source_arrays(pools, parent, p, m, b['weights'])
            rebuilt = {d['id']: verify_node(b['nodes'][d['id']], d, *spaces[d['geometry']], y, rpm, cr, ix, a['seed']) for d in MODELS}
            cells.append(dict(fold_id=a['fold_id'], seed=a['seed'], model_sha256=a['sha256'], verified=rebuilt))
            logger.info('來源重建 {} seed{}', a['fold_id'], a['seed'])
    after = verify_sources(pools.root, context[3][0])
    if before != after:
        raise ValueError('formal data changed')
    result = seal(dict(protocol_checksum=p['protocol_checksum'], locked_checksum=lock['locked_checksum'], cells=cells,
                      source_before=before, source_after=after, test_numeric_reads=0, fresh_final_test=False,
                      status='VERIFIED_AVAILABLE_NUMERIC_SOURCES'), 'source_verification_checksum')
    save_json(output/'source_verified.json', result)
    return result


def infer(parent, b, X, rpm):
    H = parent['references']['harmonic69/mixed']['transformer'].transform(X)
    spaces = {'identity': H, 'metric': weight_transform(H, b['weights'])}
    base = parent['references']['base75/mixed']
    score = base['detectors']['mahalanobis'].score_samples(base['transformer'].transform(X))
    return {a['id']: (b['nodes'][d['id']]['model'].predict(spaces[d['geometry']], rpm), score, 1.)
            for d, a in zip(MODELS, ARMS) if b['nodes'][d['id']]['status'] == 'completed'}


def evaluate(pools, p, lock, source, output, evaluation=None):
    context = check(p)
    validate_parent_source(p, lock, source)
    verify = evaluation is not None
    if verify:
        verify_seal(evaluation, 'evaluation_checksum')
        if any(evaluation[k] != v for k, v in [('protocol_checksum', p['protocol_checksum']),
            ('locked_checksum', lock['locked_checksum']), ('source_verification_checksum', source['source_verification_checksum'])]):
            raise ValueError('context evaluation source binding')
    before = verify_sources(pools.root, context[3][0])
    start, runs, failed, unique = time.perf_counter(), [], [], set()
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start)
            m = next(x for x in context[3] if x['fold_id'] == a['fold_id'])
            b, parent, _ = load_model(a, p, m, context)
            rr = records_for(m, 'test')
            X, rpm = pools.load(rr), rpm_values(rr)
            t = time.perf_counter()
            values = infer(parent, b, X, rpm)
            seconds = time.perf_counter()-t
            mutated = [dict(r, label='MUTATED_TRUTH') for r in rr]
            changed = pools.load(mutated)
            if not np.array_equal(X, changed) or not np.array_equal(rpm, rpm_values(mutated)):
                raise ValueError('truth entered context inputs')
            if verify:
                second = infer(parent, b, changed, rpm_values(mutated))
                if any(not np.array_equal(values[k][j], second[k][j]) for k in values for j in [0, 1]):
                    raise ValueError('truth entered context inference')
            for d in ARMS:
                rid = d['id']+'_'+a['fold_id']+'_seed'+str(a['seed'])
                cp = output/(rid+'.checkpoint.json')
                if d['id'] not in values:
                    failed.append(dict(run_id=rid, arm_id=d['id'], fold_id=a['fold_id'], seed=a['seed'], status='INCOMPLETE',
                                       reason=b['nodes'][d['model']]['model'].optimizer_['message']))
                    continue
                pred, score, threshold = values[d['id']]
                if verify or cp.exists():
                    r = next(x for x in evaluation['runs'] if x['run_id'] == rid) if verify else read(cp)
                    verify_seal(r, 'checkpoint_checksum')
                    rows = predictions(r)
                    check_rows(rows, r, m, p, lock)
                    if (r['model_artifact'] != a or not np.array_equal(pred, [p['known_labels'].index(x['predicted_known_class']) for x in rows]) or
                            not np.array_equal(score, [x['openset_score'] for x in rows]) or any(x['threshold'] != threshold for x in rows)):
                        raise ValueError('context reinference mismatch')
                else:
                    rows = make_rows(rr, pred, score, threshold, p['known_labels'], d['id'], a['sha256'], p['protocol_checksum'], lock['locked_checksum'])
                    for row in rows:
                        row.update(seed=a['seed'], split_sha=m['manifest_checksum'], final_decision=decision(row['predicted_known_class'], row['openset_score'], threshold))
                    path = output/(rid+'.jsonl.gz')
                    path.write_bytes(gzip.compress('\n'.join(json.dumps(x, sort_keys=True, allow_nan=False) for x in rows).encode(), compresslevel=3, mtime=0))
                    r = dict(run_id=rid, arm_id=d['id'], fold_id=a['fold_id'], seed=a['seed'], motor_roles=m['motor_roles'], samples=len(rows),
                             model_artifact=a, prediction_artifact=artifact(path), threshold=threshold, test_ids_checksum=digest(m['sample_ids']['test']),
                             protocol_checksum=p['protocol_checksum'], locked_checksum=lock['locked_checksum'], status='completed',
                             shared_bundle_inference_seconds=seconds, process_peak_memory_bytes=peak_memory_bytes())
                    r.update(summarized(rows, p))
                    check_rows(rows, r, m, p, lock)
                    r = seal(r, 'checkpoint_checksum')
                    save_json(cp, r)
                runs.append(r)
                unique.update(x['sample_id'] for x in rows)
            logger.info('配對 {} seed{}，完成{}方法', a['fold_id'], a['seed'], len(values))
    after = verify_sources(pools.root, context[3][0])
    ids = [r['run_id'] for r in runs+failed]
    if before != after or len(ids) != 108 or len(set(ids)) != 108 or (verify and failed != evaluation['failed_runs']):
        raise ValueError('source/matrix/failure inventory mismatch')
    key, name = ('verification_checksum', 'verified') if verify else ('evaluation_checksum', 'evaluation')
    result = seal(dict(protocol_checksum=p['protocol_checksum'], locked_checksum=lock['locked_checksum'], source_verification_checksum=source['source_verification_checksum'],
        runs=runs, failed_runs=failed, planned_runs=108, completed_runs=len(runs), prediction_records=sum(r['samples'] for r in runs),
        unique_samples=len(unique), source_before=before, source_after=after, seconds=time.perf_counter()-start,
        fresh_final_test=False, scope=p['scope']), key)
    result = save_immutable(output/(name+'.json'), result, key)
    write_gzip(output/(name+'.json.gz'), result)
    return result


def report(p, e, v, baseline, previous, euclidean, output):
    context = check(p)
    for obj, key in [(e, 'evaluation_checksum'), (v, 'verification_checksum'), (baseline, 'metrics_checksum'),
                     (previous, 'evaluation_checksum'), (euclidean, 'evaluation_checksum')]:
        verify_seal(obj, key)
    if (e['runs'] != v['runs'] or e['failed_runs'] != v['failed_runs'] or e['protocol_checksum'] != p['protocol_checksum'] or
            v['protocol_checksum'] != p['protocol_checksum'] or v['locked_checksum'] != e['locked_checksum'] or
            v['source_verification_checksum'] != e['source_verification_checksum'] or baseline['protocol_checksum'] != p['parent_protocol_checksum'] or
            euclidean['protocol_checksum'] != context[0]['protocol_checksum'] or euclidean['locked_checksum'] != read(p['parent_lock']['path'])['locked_checksum']):
        raise ValueError('context report binding')
    controls = {c: [r for r in baseline['runs'] if r['arm_id'] == c and r['score_id'] == 'mahalanobis'] for c in ['C02', 'C17', 'C24']}
    controls['D01'] = [r for r in previous['runs'] if r['arm_id'] == 'D01']
    matched = {a['id']: ('G01' if d['geometry'] == 'identity' else 'G13') if d['variant'] == 'static' else
               ('G03' if d['geometry'] == 'identity' else 'G15') for d, a in zip(MODELS, ARMS)}
    controls.update({g: [r for r in euclidean['runs'] if r['arm_id'] == g] for g in set(matched.values())})
    groups = dict(controls, **{a['id']: [r for r in e['runs'] if r['arm_id'] == a['id']] for a in ARMS})
    tables, gates, signatures = {}, {}, {}
    for name, rr in groups.items():
        if len(rr) != 9:
            tables[name] = dict(status='INCOMPLETE', completed_runs=len(rr), failures=[r for r in e['failed_runs'] if r['arm_id'] == name])
            continue
        rows, derived, final_by_group = [], [], []
        for r in rr:
            x = predictions(r)
            recomputed = summarized(x, p)
            if recomputed['metrics'] != r['metrics'] or recomputed['rpm_metrics'] != r['rpm_metrics']:
                raise ValueError('context saved metrics mismatch')
            signatures[name, r['fold_id'], r['seed']] = digest([[a['sample_id'], a['true_label'], a['source_sha256']] for a in x])
            truth = ['unknown' if a['true_label'] in p['unknown_labels'] else a['true_label'] for a in x]
            final = [decision(a['predicted_known_class'], a['openset_score'], a['threshold']) for a in x]
            final_by_group.append(dict(motor=r['motor_roles']['test'], seed=r['seed'], samples=len(x),
                classification=classification(truth, final, p['known_labels']+['unknown'], p['known_labels'][1:])))
            derived.append(dict(r, configuration_metrics=recomputed['configuration_metrics']))
            if r['seed'] == 0:
                rows += x
        if len(rows) != 28910 or len({r['sample_id'] for r in rows}) != 28910:
            raise ValueError('context unique samples mismatch')
        tables[name] = summarize(derived, rows, p)
        tables[name]['final_fault_all_samples_by_motor_seed'] = final_by_group
        truth = ['unknown' if r['true_label'] in p['unknown_labels'] else r['true_label'] for r in rows]
        final = [decision(r['predicted_known_class'], r['openset_score'], r['threshold']) for r in rows]
        tables[name]['final_fault_all_samples'] = classification(truth, final, p['known_labels']+['unknown'], p['known_labels'][1:])
        tables[name]['conditional_fault_f1_scope'] = '僅true known faulty；完整final分母另列'
        if name not in controls:
            gates[name] = assess(derived, {k: controls[k] for k in ['C02', 'C17', 'C24', 'D01']}, CONTRACT)
        logger.info('重算 {} 共9格', name)
    comparisons = [(a['id'], c) for a in ARMS for c in ['C02', 'C17', 'C24', 'D01', matched[a['id']]]]
    for i, d in enumerate(MODELS):
        if d['variant'] != 'static':
            comparisons.append((ARMS[i]['id'], ARMS[i-1]['id']))
        if d['degree'] == 2:
            comparisons.append((ARMS[i]['id'], ARMS[i-3]['id']))
        if d['geometry'] == 'metric':
            comparisons.append((ARMS[i]['id'], ARMS[i-6]['id']))
    pairs = []
    for new, old in comparisons:
        for r in groups[new]:
            prior = next((x for x in groups[old] if (x['fold_id'], x['seed']) == (r['fold_id'], r['seed'])), None)
            if prior is None:
                continue
            key = (r['fold_id'], r['seed'])
            if signatures[(new,)+key] != signatures[(old,)+key]:
                raise ValueError('context paired ID/truth/source mismatch')
            pairs.append(dict(method=new, control=old, fold_id=r['fold_id'], seed=r['seed'], samples=r['samples'],
                              paired_id_truth_source_checksum=signatures[(new,)+key],
                              fault_accuracy_delta_pp=100*(r['metrics']['known_fault_classification']['accuracy']-prior['metrics']['known_fault_classification']['accuracy'])))
    result = seal(dict(protocol_checksum=p['protocol_checksum'], evaluation_checksum=e['evaluation_checksum'], verification_checksum=v['verification_checksum'],
        euclidean_evaluation_checksum=euclidean['evaluation_checksum'], methods=tables, reliability=gates, paired_differences=pairs,
        completed_runs=e['completed_runs'], failed_runs=e['failed_runs'], prediction_records=e['prediction_records'], unique_samples=e['unique_samples'],
        subsets_tested=1, fresh_final_test=False, production_replacement=False,
        conclusion='固定工況原型探索比較；無global winner，來源UNKNOWN、final guard INCOMPLETE'), 'report_checksum')
    save_json(output/'summary.json', result)
    write_gzip(output/'summary.json.gz', result)
    return result


def run(pools, *, action, p, output, lock=None, source_verification=None, evaluation=None, verification=None,
        baseline=None, previous=None, euclidean=None):
    if action == 'fit':
        return fit(pools, p, output)
    if action == 'source-verify':
        return source_verify(pools, p, lock, output)
    if action in ['evaluate', 'verify']:
        return evaluate(pools, p, lock, source_verification, output, evaluation if action == 'verify' else None)
    if action == 'report':
        return report(p, evaluation, verification, baseline, previous, euclidean, output)
    raise ValueError('unsupported action')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['lock', 'fit', 'source-verify', 'evaluate', 'verify', 'report', 'smoke', 'backup'])
    for key in ['parent-protocol', 'parent-lock', 'parent-source', 'protocol', 'lock', 'source-verification', 'evaluation',
                'verification', 'baseline', 'previous', 'euclidean', 'data-root', 'resume']:
        parser.add_argument('--'+key, type=Path)
    parser.add_argument('--archive-root', type=Path, action='append')
    a = parser.parse_args()
    log, paths = setup_run('fault_type_context_prototypes_'+a.action.replace('-', '_'))
    out = paths.output_dir
    if a.action in ['fit', 'evaluate', 'verify']:
        out = BASE/paths.output_dir.parent.name/paths.output_dir.name
        out.mkdir(parents=True, exist_ok=False)
    if a.resume:
        candidate = a.resume.resolve()
        if candidate.parent != BASE.resolve()/paths.output_dir.parent.name or not candidate.is_dir():
            raise ValueError('same-action explicit context resume root')
        out = candidate
    if a.action == 'backup':
        if not a.archive_root:
            parser.error('archive-root required')
        roots = [r.resolve() for r in a.archive_root]
        if len({r.name for r in roots}) != len(roots) or any(BASE.resolve() not in r.parents or not r.is_dir() or
            not any((r/n).is_file() for n in ['locked_study.json', 'evaluation.json', 'verified.json']) for r in roots):
            raise ValueError('only completed unique context outputs')
        from experiments.fault_type_archive import run as archive
        from experiments.fault_type_fixed_delivery import run as verify_archive
        result = archive(roots, destination=BASE.parents[1]/'archives', paths=paths, log=log)
        save_json(out/'member_verification.json', verify_archive(None, indices=[out/'archive_index.json']))
    elif a.action == 'lock':
        if any(getattr(a, k) is None for k in ['parent_protocol', 'parent_lock', 'parent_source']):
            parser.error('parent sources required')
        result = build(a.parent_protocol, a.parent_lock, a.parent_source)
        check(result)
        save_json(out/'protocol.json', result)
    elif a.action == 'smoke':
        rng = np.random.default_rng(42)
        rpm = np.tile(np.repeat(RPMS, 10), 2)
        y = np.repeat([0, 1], 30)
        X = y[:, None]*2-1+((rpm-8000)/3000)[:, None]*np.array([3., -.5, 2.])+rng.normal(0, .05, (60, 3))
        models = {d: ContextPrototypes(d, 'auxiliary', 42).fit(X, y, rpm, np.arange(60)) for d in [1, 2]}
        if any(not m.optimizer_['success'] for m in models.values()):
            raise ValueError('synthetic context optimizer failed')
        result = dict(scope='SYNTHETIC_ENGINEERING_ONLY', models={str(k): dict(state_checksum=m.checksum_, optimizer=m.optimizer_) for k, m in models.items()})
        save_json(out/'smoke.json', result)
    else:
        if not a.protocol:
            parser.error('protocol required')
        required = {'fit': ['data_root'], 'source-verify': ['lock', 'data_root'],
                    'evaluate': ['lock', 'data_root', 'source_verification'],
                    'verify': ['lock', 'data_root', 'source_verification', 'evaluation'],
                    'report': ['evaluation', 'verification', 'baseline', 'previous', 'euclidean']}[a.action]
        if any(getattr(a, k) is None for k in required):
            parser.error('missing '+','.join(required))
        kwargs = {k: read(getattr(a, k)) if getattr(a, k) else None for k in ['lock', 'source_verification', 'evaluation', 'verification', 'baseline', 'previous', 'euclidean']}
        result = run(FeatureStore(a.data_root) if a.data_root else None, action=a.action, p=read(a.protocol), output=out, **kwargs)
    if a.action in ['fit', 'evaluate', 'verify']:
        name = {'fit': 'locked_study.json', 'evaluate': 'evaluation.json.gz', 'verify': 'verified.json.gz'}[a.action]
        shutil.copyfile(out/name, paths.output_dir/name)
        save_json(paths.output_dir/'artifact_location.json', dict(primary_output=str(out.resolve()), compact_artifact=artifact(paths.output_dir/name),
            primary_artifact=artifact(out/name), contains_raw_data=False))
    log.info('{} 完成，輸出 {}', a.action, out)


if __name__ == '__main__':
    main()
