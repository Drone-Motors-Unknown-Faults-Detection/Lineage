"""實驗18：固定RPM原型距離與歧義拒絕；來源見先行手冊。"""
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
from core.fault_type_context_rejection import ContextRejection, components, MODES, EPSILON
from experiments import fault_type_context_prototypes as I
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
from experiments.fault_type_smooth_l1 import validate_parent_source
from experiments.fault_type_fixed_calibration import verify_sources
from experiments.fault_type_literature_study import artifact, write_gzip, read_gzip, make_rows
from experiments.fault_type_mechanism_study import summarized, check_rows, save_immutable
from experiments.fault_type_mechanism_report import predictions, summarize


MODELS = [dict(id=d['id']+'_'+mode, parent_model=d['id'], parent_arm=a['id'], mode=mode)
          for d, a in zip(I.MODELS, I.ARMS) for mode in MODES]
ARMS = [dict(id=f'J{i+1:02}', model=d['id'], detector=d['mode'], parent_arm=d['parent_arm']) for i, d in enumerate(MODELS)]
PARAMETERS = dict(models=MODELS, quantile=.95, quantile_method='linear', epsilon=EPSILON,
                  threshold=0., reject_comparison='strict >', calibration_scope='pooled known calibration motor',
                  unknown_score_direction='higher', fusion='max signed normalized excess')
BUDGET = dict(planned_runs=324, seconds_per_action=1800, reserve_C_bytes=1000000000)
FILES = ['core/fault_type_context_rejection.py', 'experiments/fault_type_context_rejection.py',
         'docs/experiments/exp18_context_rejection.md']
BASE = Path('D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/context_rejection_v1/workspace/output')
read = I.read


def build(protocol, lock, source_path):
    ip, il, source = read(protocol), read(lock), read(source_path)
    I.check(ip)
    validate_parent_source(ip, il, source)
    p = {k: ip[k] for k in I.KEYS}
    p.update(version='exp18_context_rejection_v1', parent_protocol=artifact(protocol), parent_lock=artifact(lock),
        parent_source=artifact(source_path), parameters=PARAMETERS, arms=ARMS, budget=BUDGET,
        environment={'python': platform.python_version(), 'sklearn': sklearn.__version__},
        implementations=[artifact(Path(f)) for f in FILES], selection_policy='none', selection_sample_ids=[],
        validation_sample_ids=[], shared_validation_calibration=False, fresh_final_test=False,
        scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED',
        source_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
    return seal(p, 'protocol_checksum')


def check(p):
    verify_seal(p, 'protocol_checksum')
    I.validate_policy(p)
    if (p['version'] != 'exp18_context_rejection_v1' or p['parameters'] != PARAMETERS or p['arms'] != ARMS or
            p['budget'] != BUDGET or p['reliability_contract'] != CONTRACT):
        raise ValueError('fixed rejection definitions changed')
    if p['environment'] != {'python': platform.python_version(), 'sklearn': sklearn.__version__}:
        raise ValueError('native rejection environment required')
    if [a['path'] for a in p['implementations']] != [str(Path(f).resolve()) for f in FILES]:
        raise ValueError('source inventory')
    for a in p['implementations']+[p['parent_protocol'], p['parent_lock'], p['parent_source']]:
        if _sha256_file(Path(a['path'])) != a['sha256']:
            raise ValueError('rejection source SHA')
    ip, il, source = [read(p[k]['path']) for k in ['parent_protocol', 'parent_lock', 'parent_source']]
    ic = I.check(ip)
    validate_parent_source(ip, il, source)
    if any(p[k] != ip[k] for k in I.KEYS):
        raise ValueError('rejection parent binding')
    return ip, il, source, ic


def parent_for(p, m, seed, context):
    ip, il, source, ic = context
    ia = next(a for a in il['artifacts'] if (a['fold_id'], a['seed']) == (m['fold_id'], seed))
    b, parent, ix = I.load_model(ia, ip, m, ic)
    return ia, b, parent, ix


def expected_audits(p, m, b):
    tr, ca = records_for(m, 'train'), records_for(m, 'calibration')
    check_cell(tr, ca, p['known_labels'])
    ids, cis = [r['sample_id'] for r in tr], [r['sample_id'] for r in ca]
    if set(ids)&set(cis) or set(ids+cis)&set(m['sample_ids']['test']) or len(set(m['motor_roles'].values())) != 3:
        raise ValueError('rejection motor/sample purpose overlap')
    audits = []
    for d, arm in zip(MODELS, ARMS):
        prior = next(x for x in b['audits'] if x['definition']['model'] == d['parent_model'])
        if (any(prior[k] != ids for k in ['scaler_fit_ids', 'representation_fit_ids', 'classifier_fit_ids', 'reference_fit_ids', 'context_fit_ids']) or
                prior['calibration_sample_ids'] != cis or prior['selection_sample_ids'] or
                prior['selection_policy'] != 'none' or prior['shared_validation_calibration']):
            raise ValueError('inherited classifier fit/cal purpose')
        audits.append(dict(prior, definition=arm, parent_definition=prior['definition'],
            protocol_checksum=p['protocol_checksum'], detector_calibration_ids=cis, quantile=.95, quantile_method='linear',
            detector_source='fixed context distances; known calibration only', new_classifier_fit=False))
    return audits


def calibrate_nodes(b, spaces, rpm, cr):
    cached = {}
    for definition in I.MODELS:
        node = b['nodes'][definition['id']]
        if node['status'] != 'completed':
            raise ValueError('INCOMPLETE parent model; cannot calibrate')
        Z, C = spaces[definition['geometry']]
        model = node['model']
        train_d, cal_d = model.distances(Z, rpm), model.distances(C, cr)
        cached[definition['id']] = (train_d, cal_d, model.checksum_)
    result = {}
    for d in MODELS:
        train_d, cal_d, signature = cached[d['parent_model']]
        model = ContextRejection(d['mode']).calibrate(cal_d)
        result[d['id']] = dict(model=model, status='completed', parent_model_state_checksum=signature,
            train_distances_checksum=digest(train_d.tolist()), calibration_distances_checksum=digest(cal_d.tolist()),
            calibration_scores_checksum=digest(model.score_samples(cal_d).tolist()))
    return result


def verify_nodes(nodes, b, spaces, rpm, cr):
    expected = calibrate_nodes(b, spaces, rpm, cr)
    if set(nodes) != set(expected):
        raise ValueError('rejection node inventory')
    for key, value in expected.items():
        n = nodes[key]
        if (n['model'].signature() != n['model'].checksum_ or n['model'].checksum_ != value['model'].checksum_ or
                any(n[k] != value[k] for k in value if k != 'model')):
            raise ValueError('actual known calibration/parent distance mismatch')
    return {k: dict(state_checksum=v['model'].checksum_, quantiles=v['model'].quantiles_.tolist(),
                    calibration_distances_checksum=v['calibration_distances_checksum']) for k, v in expected.items()}


def budget(start):
    if time.perf_counter()-start > BUDGET['seconds_per_action'] or shutil.disk_usage('C:/').free < BUDGET['reserve_C_bytes']:
        raise RuntimeError('rejection budget; preserve checkpoints')


def load_model(a, p, m, context):
    for f in [a, a['fit_audits']]:
        if _sha256_file(Path(f['path'])) != f['sha256']:
            raise ValueError('rejection model/audit SHA')
    b = joblib.load(a['path'])
    ia, ib, parent, ix = parent_for(p, m, a['seed'], context)
    if (b['protocol_checksum'] != p['protocol_checksum'] or b['manifest_checksum'] != m['manifest_checksum'] or
            b['seed'] != a['seed'] or b['parent_sha256'] != ia['sha256'] or a['parent_artifact'] != ia or
            b['audits'] != expected_audits(p, m, ib) or read_gzip(a['fit_audits']['path']) != b['audits'] or
            set(b['nodes']) != {d['id'] for d in MODELS}):
        raise ValueError('rejection model/source binding')
    for d in MODELS:
        n = b['nodes'][d['id']]
        if (n['status'] != 'completed' or n['model'].mode != d['mode'] or n['model'].signature() != n['model'].checksum_ or
                n['parent_model_state_checksum'] != ib['nodes'][d['parent_model']]['model'].checksum_):
            raise ValueError('rejection definition/state')
    return b, ib, parent, ix


def calibrate(pools, p, output):
    context = check(p)
    ms, il = context[3][3], context[1]
    before = verify_sources(pools.root, ms[0])
    start, arts = time.perf_counter(), []
    with threadpool_limits(limits=1):
        for ia in il['artifacts']:
            budget(start)
            m = next(x for x in ms if x['fold_id'] == ia['fold_id'])
            cell = output/(m['fold_id']+'_seed'+str(ia['seed']))
            cell.mkdir(exist_ok=True)
            cp = cell/'checkpoint.json'
            if cp.exists():
                saved = read(cp)
                verify_seal(saved, 'checkpoint_checksum')
                load_model(saved['artifact'], p, m, context)
                arts.append(saved['artifact'])
                continue
            t = time.perf_counter()
            ia, ib, parent, ix = parent_for(p, m, ia['seed'], context)
            y, spaces, rpm, cr = I.source_arrays(pools, parent, context[0], m, ib['weights'])
            nodes = calibrate_nodes(ib, spaces, rpm, cr)
            b = dict(protocol_checksum=p['protocol_checksum'], manifest_checksum=m['manifest_checksum'], seed=ia['seed'],
                     parent_sha256=ia['sha256'], nodes=nodes, audits=expected_audits(p, m, ib))
            joblib.dump(b, cell/'model.joblib', compress=3)
            write_gzip(cell/'fit_audits.json.gz', b['audits'])
            a = dict(artifact(cell/'model.joblib'), fold_id=m['fold_id'], seed=ia['seed'], parent_artifact=ia,
                fit_audits=artifact(cell/'fit_audits.json.gz'), seconds=time.perf_counter()-t, process_peak_memory_bytes=peak_memory_bytes())
            load_model(a, p, m, context)
            save_json(cp, seal(dict(artifact=a, protocol_checksum=p['protocol_checksum']), 'checkpoint_checksum'))
            arts.append(a)
            logger.info('固定calibration {}，36拒絕器，0新classifier fit', cell.name)
    after = verify_sources(pools.root, ms[0])
    if before != after:
        raise ValueError('formal data changed')
    return save_immutable(output/'locked_study.json', seal(dict(protocol_checksum=p['protocol_checksum'], artifacts=arts,
        source_before=before, source_after=after, environment=p['environment'], selection_policy='none', selection_sample_ids=[],
        new_classifier_fits=0, calibration_nodes=324,
        code_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()), 'locked_checksum'), 'locked_checksum')


def source_verify(pools, p, lock, output):
    context = check(p)
    G.validate_lock(p, lock)
    before = verify_sources(pools.root, context[3][3][0])
    start, cells = time.perf_counter(), []
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start)
            m = next(x for x in context[3][3] if x['fold_id'] == a['fold_id'])
            b, ib, parent, ix = load_model(a, p, m, context)
            y, spaces, rpm, cr = I.source_arrays(pools, parent, context[0], m, ib['weights'])
            values = verify_nodes(b['nodes'], ib, spaces, rpm, cr)
            cells.append(dict(fold_id=a['fold_id'], seed=a['seed'], model_sha256=a['sha256'], verified=values))
            logger.info('重建known cal {} seed{}', a['fold_id'], a['seed'])
    after = verify_sources(pools.root, context[3][3][0])
    if before != after:
        raise ValueError('formal data changed')
    result = seal(dict(protocol_checksum=p['protocol_checksum'], locked_checksum=lock['locked_checksum'], cells=cells,
        source_before=before, source_after=after, test_numeric_reads=0, new_classifier_fits=0,
        parent_actual_source_verification=context[2]['source_verification_checksum'],
        status='VERIFIED_AVAILABLE_NUMERIC_SOURCES', fresh_final_test=False), 'source_verification_checksum')
    save_json(output/'source_verified.json', result)
    return result


def infer(parent, b, ib, X, rpm):
    H = parent['references']['harmonic69/mixed']['transformer'].transform(X)
    spaces = {'identity': H, 'metric': weight_transform(H, ib['weights'])}
    predictions_by_model, distances_by_model = {}, {}
    for d in I.MODELS:
        model = ib['nodes'][d['id']]['model']
        distances = model.distances(spaces[d['geometry']], rpm)
        distances_by_model[d['id']] = distances
        predictions_by_model[d['id']] = model.labels_[np.argmin(distances, axis=1)]
    result = {}
    for d, a in zip(MODELS, ARMS):
        distances = distances_by_model[d['parent_model']]
        rejector = b['nodes'][d['id']]['model']
        result[a['id']] = (predictions_by_model[d['parent_model']], rejector.score_samples(distances), 0.,
            dict(raw=components(distances), quantiles=rejector.quantiles_.tolist(), state_checksum=rejector.checksum_, mode=d['mode']))
    return result


def evaluate(pools, p, lock, source, output, evaluation=None):
    context = check(p)
    validate_parent_source(p, lock, source)
    verify = evaluation is not None
    if verify:
        verify_seal(evaluation, 'evaluation_checksum')
        if any(evaluation[k] != v for k, v in [('protocol_checksum', p['protocol_checksum']),
            ('locked_checksum', lock['locked_checksum']), ('source_verification_checksum', source['source_verification_checksum'])]):
            raise ValueError('rejection evaluation source binding')
    before = verify_sources(pools.root, context[3][3][0])
    start, runs, failed, unique = time.perf_counter(), [], [], set()
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start)
            m = next(x for x in context[3][3] if x['fold_id'] == a['fold_id'])
            b, ib, parent, _ = load_model(a, p, m, context)
            rr = records_for(m, 'test')
            X, rpm = pools.load(rr), I.rpm_values(rr)
            t = time.perf_counter()
            values = infer(parent, b, ib, X, rpm)
            seconds = time.perf_counter()-t
            mutated = [dict(r, label='MUTATED_TRUTH') for r in rr]
            changed = pools.load(mutated)
            if not np.array_equal(X, changed) or not np.array_equal(rpm, I.rpm_values(mutated)):
                raise ValueError('truth entered rejection inputs')
            if verify:
                second = infer(parent, b, ib, changed, I.rpm_values(mutated))
                if any(not np.array_equal(values[k][j], second[k][j]) for k in values for j in [0, 1]):
                    raise ValueError('truth entered rejection inference')
            for d in ARMS:
                rid = d['id']+'_'+a['fold_id']+'_seed'+str(a['seed'])
                cp = output/(rid+'.checkpoint.json')
                if d['id'] not in values:
                    failed.append(dict(run_id=rid, arm_id=d['id'], fold_id=a['fold_id'], seed=a['seed'], status='INCOMPLETE',
                                       reason='INCOMPLETE_PARENT_OR_CALIBRATION'))
                    continue
                pred, score, threshold, extra = values[d['id']]
                if verify or cp.exists():
                    r = next(x for x in evaluation['runs'] if x['run_id'] == rid) if verify else read(cp)
                    verify_seal(r, 'checkpoint_checksum')
                    rows = predictions(r)
                    check_rows(rows, r, m, p, lock)
                    if (r['model_artifact'] != a or not np.array_equal(pred, [p['known_labels'].index(x['predicted_known_class']) for x in rows]) or
                            not np.array_equal(score, [x['openset_score'] for x in rows]) or any(x['threshold'] != threshold for x in rows)):
                        raise ValueError('rejection reinference mismatch')
                    check_components(rows, extra)
                else:
                    rows = make_rows(rr, pred, score, threshold, p['known_labels'], d['id'], a['sha256'], p['protocol_checksum'], lock['locked_checksum'])
                    for j, row in enumerate(rows):
                        row.update(seed=a['seed'], split_sha=m['manifest_checksum'], final_decision=decision(row['predicted_known_class'], row['openset_score'], threshold),
                            context_distance=float(extra['raw'][j, 0]), context_ambiguity=float(extra['raw'][j, 1]),
                            calibration_quantiles=extra['quantiles'], rejector_state_checksum=extra['state_checksum'], score_mode=extra['mode'])
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
    after = verify_sources(pools.root, context[3][3][0])
    ids = [r['run_id'] for r in runs+failed]
    if before != after or len(ids) != 324 or len(set(ids)) != 324 or (verify and failed != evaluation['failed_runs']):
        raise ValueError('source/matrix/failure inventory mismatch')
    key, name = ('verification_checksum', 'verified') if verify else ('evaluation_checksum', 'evaluation')
    result = seal(dict(protocol_checksum=p['protocol_checksum'], locked_checksum=lock['locked_checksum'], source_verification_checksum=source['source_verification_checksum'],
        runs=runs, failed_runs=failed, planned_runs=324, completed_runs=len(runs), prediction_records=sum(r['samples'] for r in runs),
        unique_samples=len(unique), source_before=before, source_after=after, seconds=time.perf_counter()-start,
        fresh_final_test=False, scope=p['scope']), key)
    result = save_immutable(output/(name+'.json'), result, key)
    write_gzip(output/(name+'.json.gz'), result)
    return result


def check_components(rows, extra):
    if (not np.array_equal(extra['raw'], [[x['context_distance'], x['context_ambiguity']] for x in rows]) or
            any(x['calibration_quantiles'] != extra['quantiles'] or x['rejector_state_checksum'] != extra['state_checksum'] or
                x['score_mode'] != extra['mode'] for x in rows)):
        raise ValueError('saved raw rejection components/quantiles mismatch')


def report(p, e, v, baseline, previous, parent_evaluation, output):
    context = check(p)
    for obj, key in [(e, 'evaluation_checksum'), (v, 'verification_checksum'), (baseline, 'metrics_checksum'),
                     (previous, 'evaluation_checksum'), (parent_evaluation, 'evaluation_checksum')]:
        verify_seal(obj, key)
    if (e['runs'] != v['runs'] or e['failed_runs'] != v['failed_runs'] or e['protocol_checksum'] != p['protocol_checksum'] or
            v['protocol_checksum'] != p['protocol_checksum'] or v['locked_checksum'] != e['locked_checksum'] or
            v['source_verification_checksum'] != e['source_verification_checksum'] or baseline['protocol_checksum'] != p['parent_protocol_checksum'] or
            parent_evaluation['protocol_checksum'] != context[0]['protocol_checksum'] or parent_evaluation['locked_checksum'] != context[1]['locked_checksum']):
        raise ValueError('rejection report binding')
    controls = {c: [r for r in baseline['runs'] if r['arm_id'] == c and r['score_id'] == 'mahalanobis'] for c in ['C02', 'C17', 'C24']}
    controls['D01'] = [r for r in previous['runs'] if r['arm_id'] == 'D01']
    matched = {a['id']: a['parent_arm'] for a in ARMS}
    controls.update({a['id']: [r for r in parent_evaluation['runs'] if r['arm_id'] == a['id']] for a in I.ARMS})
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
                raise ValueError('rejection saved metrics mismatch')
            signatures[name, r['fold_id'], r['seed']] = digest([[a['sample_id'], a['true_label'], a['source_sha256']] for a in x])
            truth = ['unknown' if a['true_label'] in p['unknown_labels'] else a['true_label'] for a in x]
            final = [decision(a['predicted_known_class'], a['openset_score'], a['threshold']) for a in x]
            final_by_group.append(dict(motor=r['motor_roles']['test'], seed=r['seed'], samples=len(x),
                classification=classification(truth, final, p['known_labels']+['unknown'], p['known_labels'][1:])))
            derived.append(dict(r, configuration_metrics=recomputed['configuration_metrics']))
            if r['seed'] == 0:
                rows += x
        if len(rows) != 28910 or len({r['sample_id'] for r in rows}) != 28910:
            raise ValueError('rejection unique samples mismatch')
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
        if d['mode'] != 'distance':
            comparisons.append((ARMS[i]['id'], ARMS[i-i%3]['id']))
    pairs = []
    for new, old in comparisons:
        for r in groups[new]:
            prior = next((x for x in groups[old] if (x['fold_id'], x['seed']) == (r['fold_id'], r['seed'])), None)
            if prior is None:
                continue
            key = (r['fold_id'], r['seed'])
            if signatures[(new,)+key] != signatures[(old,)+key]:
                raise ValueError('rejection paired ID/truth/source mismatch')
            pairs.append(dict(method=new, control=old, fold_id=r['fold_id'], seed=r['seed'], samples=r['samples'],
                              paired_id_truth_source_checksum=signatures[(new,)+key],
                              fault_accuracy_delta_pp=100*(r['metrics']['known_fault_classification']['accuracy']-prior['metrics']['known_fault_classification']['accuracy'])))
    result = seal(dict(protocol_checksum=p['protocol_checksum'], evaluation_checksum=e['evaluation_checksum'], verification_checksum=v['verification_checksum'],
        parent_evaluation_checksum=parent_evaluation['evaluation_checksum'], methods=tables, reliability=gates, paired_differences=pairs,
        completed_runs=e['completed_runs'], failed_runs=e['failed_runs'], prediction_records=e['prediction_records'], unique_samples=e['unique_samples'],
        subsets_tested=1, fresh_final_test=False, production_replacement=False,
        conclusion='固定工況拒絕探索比較；無global winner，來源UNKNOWN、final guard INCOMPLETE'), 'report_checksum')
    save_json(output/'summary.json', result)
    write_gzip(output/'summary.json.gz', result)
    return result


def run(pools, *, action, p, output, lock=None, source_verification=None, evaluation=None, verification=None,
        baseline=None, previous=None, parent_evaluation=None):
    if action == 'calibrate':
        return calibrate(pools, p, output)
    if action == 'source-verify':
        return source_verify(pools, p, lock, output)
    if action in ['evaluate', 'verify']:
        return evaluate(pools, p, lock, source_verification, output, evaluation if action == 'verify' else None)
    if action == 'report':
        return report(p, evaluation, verification, baseline, previous, parent_evaluation, output)
    raise ValueError('unsupported action')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['lock', 'calibrate', 'source-verify', 'evaluate', 'verify', 'report', 'smoke', 'backup'])
    for key in ['parent-protocol', 'parent-lock', 'parent-source', 'protocol', 'lock', 'source-verification', 'evaluation',
                'verification', 'baseline', 'previous', 'parent-evaluation', 'data-root', 'resume']:
        parser.add_argument('--'+key, type=Path)
    parser.add_argument('--archive-root', type=Path, action='append')
    a = parser.parse_args()
    log, paths = setup_run('fault_type_context_rejection_'+a.action.replace('-', '_'))
    out = paths.output_dir
    if a.action in ['calibrate', 'evaluate', 'verify']:
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
        cal = np.array([[1., 4.], [2., 9.], [.1, 2.]])
        query = np.array([[0., 2.], [9., 10.], [.5, .5]])
        models = {k: ContextRejection(k).calibrate(cal) for k in MODES}
        scores = {k: m.score_samples(query) for k, m in models.items()}
        if not np.array_equal(scores['or'] > 0, (scores['distance'] > 0)|(scores['ambiguity'] > 0)):
            raise ValueError('synthetic OR failed')
        result = dict(scope='SYNTHETIC_ENGINEERING_ONLY', scores={k: v.tolist() for k, v in scores.items()})
        save_json(out/'smoke.json', result)
    else:
        if not a.protocol:
            parser.error('protocol required')
        required = {'calibrate': ['data_root'], 'source-verify': ['lock', 'data_root'],
                    'evaluate': ['lock', 'data_root', 'source_verification'],
                    'verify': ['lock', 'data_root', 'source_verification', 'evaluation'],
                    'report': ['evaluation', 'verification', 'baseline', 'previous', 'parent_evaluation']}[a.action]
        if any(getattr(a, k) is None for k in required):
            parser.error('missing '+','.join(required))
        kwargs = {k: read(getattr(a, k)) if getattr(a, k) else None for k in ['lock', 'source_verification', 'evaluation', 'verification', 'baseline', 'previous', 'parent_evaluation']}
        result = run(FeatureStore(a.data_root) if a.data_root else None, action=a.action, p=read(a.protocol), output=out, **kwargs)
    if a.action in ['calibrate', 'evaluate', 'verify']:
        name = {'calibrate': 'locked_study.json', 'evaluate': 'evaluation.json.gz', 'verify': 'verified.json.gz'}[a.action]
        shutil.copyfile(out/name, paths.output_dir/name)
        save_json(paths.output_dir/'artifact_location.json', dict(primary_output=str(out.resolve()), compact_artifact=artifact(paths.output_dir/name),
            primary_artifact=artifact(out/name), contains_raw_data=False))
    log.info('{} 完成，輸出 {}', a.action, out)


if __name__ == '__main__':
    main()
