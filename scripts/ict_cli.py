#!/usr/bin/env python3
"""ICT-FSA source-local workflow. The selected commit owns its single current profile."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()

def profile():
    p = json.loads((ROOT / 'profiles/current.json').read_text())
    if p.get('schema_version') != 1 or p.get('id') not in ('U280', 'NM37', 'A70-P3', 'A100', 'A110-APB55'):
        raise ValueError('Unsupported profiles/current.json; checkout a complete milestone commit')
    if p.get('board') not in ('U280', 'NM37') or p.get('dut_mhz', 0) <= 0:
        raise ValueError('Profile board/frequency missing')
    return p

def reject_untracked_inputs(repo):
    # Ignore only known generated caches, not arbitrary .gitignore rules: an ignored
    # Scala source under src/ is still compiled by sbt.
    generated = {'target', '.venv', '__pycache__', '.bsp', '.metals', 'generated-src', 'test_run_dir', '.classpath_cache'}
    args = ['git', '-C', str(repo), 'ls-files', '--others', '-z'] + ['--exclude='+d+'/' for d in sorted(generated)]
    args += ['--exclude=generators/easyfloat/build/']
    names = subprocess.check_output(args, text=True).split('\0')
    extensions = {'.scala','.sbt','.sc','.v','.sv','.vh','.svh','.c','.cc','.cpp','.h','.hpp','.py','.sh','.tcl','.xdc','.mk'}
    unexpected = [n for n in names if n and (Path(n).suffix in extensions or Path(n).name in {'Makefile','makefile'})]
    if unexpected: raise ValueError(f'Untracked build source in {repo}: {unexpected[:20]}. Commit intended input or use a clean source checkout.')

def source_identity(p):
    # Ignored generated caches are not inputs. Tracked edits are never silently accepted.
    dirty = git('status', '--porcelain', '--untracked-files=no', '--ignore-submodules=none')
    if dirty: raise ValueError('Source/dependency changes detected. Commit intended source changes or use a clean checkout; do not reset an existing build.\n' + dirty)
    reject_untracked_inputs(ROOT)
    dependency_lock = ROOT / 'locks/dependencies.json'
    if dependency_lock.is_file():
        for name, commit in json.loads(dependency_lock.read_text())['dependencies'].items():
            dependency = ROOT / name
            if not (dependency / '.git').exists(): raise ValueError('Dependency missing: '+name+'; run deps before build')
            actual = subprocess.check_output(['git','-C',str(dependency),'rev-parse','HEAD'],text=True).strip()
            if actual != commit: raise ValueError('Dependency pin mismatch: '+name+'; preserve changes and repair with deps')
            reject_untracked_inputs(dependency)
    return {'commit': git('rev-parse', 'HEAD'), 'profile': p['id'], 'profile_sha256': sha(ROOT / 'profiles/current.json')}

def state_path(out): return out.parent / (out.name + '.ict-state')

def bind(out, p, create=False):
    if out == ROOT or out.is_relative_to(ROOT): raise ValueError('--out must be outside source checkout')
    if ' ' in str(out) or ' ' in str(ROOT): raise ValueError('Build tools require source/output paths without spaces')
    identity = source_identity(p)
    state = state_path(out)
    record = state / 'source.json'
    if record.exists():
        if json.loads(record.read_text()) != identity: raise ValueError('Output belongs to a different source/profile. Preserve it; choose a new --out')
    elif create:
        if out.exists(): raise ValueError('Unregistered output already exists. Preserve it and select a new --out')
        save(record, identity)
    else: raise ValueError('Missing build state. Run build first with this --out')
    return state

def phase_key(a): return 'sim' + str(a.array_size) if a.command == 'sim' else a.command

def run_phase(a, p):
    if a.command == 'sim' and a.array_size not in p['array_sizes']:
        raise ValueError(f"Unsupported PE array {a.array_size}; this milestone supports {p['array_sizes']}. --seq is workload length, not array size.")
    commands = p['driver']['commands'].get(a.command)
    if not commands: raise ValueError(f"{p['id']} does not have a validated {a.command} workflow. See profile/README; no stage ran.")
    out = a.out.resolve()
    values = dict(root=str(ROOT), out=str(out), array_size=a.array_size, seq=a.seq, max_cycles=getattr(a,'max_cycles',10000000))
    commands = [[str(word).format(**values) for word in command] for command in commands]
    if a.dry_run:
        print(json.dumps({'profile': p['id'], 'commands': commands, 'out': str(out), 'executed': False}, indent=2)); return
    if a.command == 'build': doctor(a, p)
    state = bind(out, p, create=a.command == 'build')
    key = phase_key(a); receipt = state / (key + '.json')
    if receipt.exists():
        old = json.loads(receipt.read_text())
        raise ValueError(f"{key} already has status={old['status']}: {receipt}. Use status and inspect its logs; preserve failed attempts. For a clean retry use a new checkout/output, reusing download caches. No command ran.")
    required = {'verify': ['build'], 'sim': ['build'], 'elaborate': ['build'],
                'implement': ['build', 'elaborate']}.get(a.command, [])
    if a.command == 'implement':
        required += ['sim'+str(n) for n in p['array_sizes']]
        if p['driver']['commands'].get('verify'): required += ['verify']
    for stage in required:
        f = state / (stage + '.json')
        if not f.is_file() or json.loads(f.read_text()).get('status') != 'completed':
            raise ValueError(f'Missing successful prerequisite {stage}. Run {stage} first; status shows failed/incomplete attempts.')
    if a.command == 'implement' and any(out.rglob('post_route.dcp')):
        raise ValueError('Routed DCP already exists before this implementation attempt; preserve it and use a new build output')
    env = dict(os.environ)
    env[p['driver']['output_env']] = str(out)
    env['ICT_BUILD_OUT'] = str(out)
    env['ICT_SOURCE'] = str(ROOT)
    env['ICT_DUT_MHZ'] = str(p['dut_mhz'])
    metadata = {'status': 'running', 'commands': commands, 'started_utc': datetime.now(timezone.utc).isoformat(), 'logs': []}
    save(receipt, metadata)
    try:
        for index, command in enumerate(commands):
            logfile = state / f'{key}-{index}.log'; metadata['logs'].append(str(logfile)); save(receipt, metadata)
            print(f'START: {key}; source checks are prerequisites, not phase completion. Log: {logfile}', flush=True)
            with logfile.open('x') as log:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            if result.returncode:
                tail = '\n'.join(logfile.read_text(errors='replace').splitlines()[-35:])
                raise RuntimeError(f'{key} exit={result.returncode}. {logfile}\n{tail}\nPreserve output/logs. Fix the environment and use a new output for a clean retry; download caches can be reused.')
        if a.command == 'sim':
            sim = out / key
            configs = list(sim.rglob('*.FSAConfig.json'))
            if len(configs) != 1 or not (sim / 'simulator').is_file():
                raise ValueError('Simulator stage exited without one binary/config pair; no successful phase is recorded')
            metadata['artifacts'] = {str(f.relative_to(out)): sha(f) for f in [sim/'simulator', configs[0]]}
        metadata['status'] = 'completed'; print('COMPLETE:', key)
    except BaseException as exc:
        metadata.update(status='failed_or_interrupted', error=str(exc)); raise
    finally:
        if a.command == 'implement':
            dcps=list(out.rglob('post_route.dcp'))
            if len(dcps)==1:
                configs=list(dcps[0].parent.parent.glob('*.FSAConfig.json'))
                if len(configs)==1:
                    metadata['routed_artifacts']={str(f.relative_to(out)):sha(f) for f in [dcps[0],configs[0]]}
                    metadata['routed_artifact_scope']='produced by this implementation attempt; backend completion/CDC acceptance remains separate'
        metadata['finished_utc'] = datetime.now(timezone.utc).isoformat(); save(receipt, metadata)

def doctor(a, p):
    checks = []
    versions = {'java':['-version'], 'firtool':['--version'], 'verilator':['--version'], 'vivado':['-version'], 'make':['--version'], 'g++':['--version']}
    for tool, arguments in versions.items():
        exe = shutil.which(tool)
        r = subprocess.run([exe, *arguments], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) if exe else None
        checks.append({'tool': tool, 'path': exe, 'ok': bool(r and r.returncode == 0 and (tool not in p.get('expected_tools', {}) or p['expected_tools'][tool] in r.stdout)), 'expected': p.get('expected_tools', {}).get(tool), 'version': r.stdout[:1000] if r else 'MISSING'})
    riscv = os.environ.get('RISCV')
    for name in ('libfesvr.a', 'libriscv.so'):
        lib = Path(riscv) / 'lib' / name if riscv else None
        checks.append({'tool': 'RISCV/'+name, 'path': str(lib) if lib else None, 'ok': bool(lib and lib.is_file() and lib.stat().st_size), 'version': 'library presence'})
    for variable, default in (('CC','gcc'),('CXX','g++')):
        exe=shutil.which(os.environ.get(variable,default))
        r=subprocess.run([exe,'-dumpfullversion'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT) if exe else None
        checks.append({'tool':variable,'path':exe,'ok':bool(r and r.returncode==0 and r.stdout.strip()=='13.3.0'),'version':r.stdout.strip() if r else 'MISSING','expected':'13.3.0'})
    if os.environ.get('JDK_JAVA_OPTIONS') or os.environ.get('_JAVA_OPTIONS') or '-Dfsa.' in os.environ.get('JAVA_TOOL_OPTIONS',''):
        checks.append({'tool':'JVM environment','ok':False,'version':'Clear inherited JDK_JAVA_OPTIONS/_JAVA_OPTIONS and hardware-specific -Dfsa.* overrides as documented'})
    print(json.dumps({'profile': p['id'], 'checks': checks, 'note': 'Tool availability only. Vendor device/license support is checked by actual implementation; version requirements are in docs/reproduction/environment.md.'}, indent=2))
    if not all(x['ok'] for x in checks): raise ValueError('Missing/failing tool. Load the documented environment before build; no build was started.')

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    deps = sub.add_parser('deps'); deps.add_argument('--offline-dir'); deps.add_argument('--local-source'); deps.add_argument('--plan', action='store_true'); deps.add_argument('--report')
    status = sub.add_parser('status'); status.add_argument('--out', type=Path, required=True)
    for name in ('build', 'verify', 'sim', 'elaborate', 'implement'):
        s = sub.add_parser(name); s.add_argument('--out', type=Path, required=True); s.add_argument('--dry-run', action='store_true')
        s.add_argument('--array-size', type=int, default=None)
        # Backend regression coverage is fixed; custom-sequence execution is explicit below.
        s.add_argument('--seq', type=int, default=None, help='Use sim-extra for a specific workload sequence')
    extra = sub.add_parser('sim-extra'); extra.add_argument('--out', type=Path, required=True); extra.add_argument('--array-size', type=int, default=None); extra.add_argument('--seq', type=int, required=True); extra.add_argument('--result-out', type=Path, required=True); extra.add_argument('--max-cycles', type=int, default=10000000)
    exp = sub.add_parser('export'); exp.add_argument('--out', type=Path, required=True, help='Existing build output'); exp.add_argument('--result-out', type=Path, required=True); exp.add_argument('--vivado', default='vivado')
    prog = sub.add_parser('program'); prog.add_argument('--export', dest='export_dir', type=Path, required=True); prog.add_argument('--hw-target', required=True, help='Exact get_hw_targets NAME, not wildcard'); prog.add_argument('--hw-device', required=True, help='Exact get_hw_devices NAME'); prog.add_argument('--server', default='localhost:3121'); prog.add_argument('--bdf', required=True, help='Operator identified PCI BDF for the selected JTAG board'); prog.add_argument('--out', type=Path, required=True); prog.add_argument('--vivado', default='vivado'); prog.add_argument('--dry-run', action='store_true')
    test = sub.add_parser('test'); test.add_argument('--receipt', type=Path, required=True); test.add_argument('--export', dest='export_dir', type=Path, required=True); test.add_argument('--device', required=True); test.add_argument('--bdf', required=True); test.add_argument('--seq', type=int, default=16); test.add_argument('--seed', type=int, default=0); test.add_argument('--repeat', type=int, default=5); test.add_argument('--warmup', type=int, default=1); test.add_argument('--out', type=Path, required=True); test.add_argument('--dry-run', action='store_true')
    summary = sub.add_parser('summarize'); summary.add_argument('results', type=Path, nargs='+'); summary.add_argument('--out', type=Path, required=True)
    a = parser.parse_args(argv); p = profile()
    if hasattr(a, 'array_size') and a.array_size is None: a.array_size = p['default_array_size']
    if a.command == 'doctor': doctor(a,p)
    elif a.command == 'deps':
        cmd = [sys.executable, str(ROOT/'scripts/ict_deps.py'), '--root', str(ROOT), '--lock', str(ROOT/'locks/dependencies.json')]
        for name in ('offline_dir','local_source','report'):
            if getattr(a,name): cmd += ['--'+name.replace('_','-'), getattr(a,name)]
        if a.plan: cmd.append('--plan')
        subprocess.run(cmd, check=True)
    elif a.command == 'status':
        state = state_path(a.out.resolve())
        if not state.exists(): print('NOT STARTED: no workflow state at',state); return
        for f in sorted(state.glob('*.json')):
            print(f.name + ': ' + json.dumps(json.loads(f.read_text()), ensure_ascii=False))
    elif a.command in ('build','verify','sim','elaborate','implement'):
        if a.seq is not None: raise ValueError('Fixed regression uses seq=array_size and 2*array_size. For seq=1024: sim-extra --array-size 16 --seq 1024 --result-out NEW_DIR')
        run_phase(a,p)
    elif a.command == 'sim-extra':
        if a.array_size not in p['array_sizes'] or a.seq <= 0 or a.seq % a.array_size or a.max_cycles <= 0: raise ValueError('Invalid array/sequence/max-cycles')
        state=bind(a.out.resolve(),p)
        record=state/f'sim{a.array_size}.json'
        if not record.is_file():raise ValueError('Complete sim for this array before sim-extra')
        stage_record=json.loads(record.read_text())
        if stage_record.get('status')!='completed' or not stage_record.get('artifacts'):raise ValueError('sim-extra requires completed sim with recorded binary/config hashes')
        for relative,digest in stage_record['artifacts'].items():
            artifact=(a.out.resolve()/relative).resolve()
            if not artifact.is_relative_to(a.out.resolve()) or not artifact.is_file() or sha(artifact)!=digest:
                raise ValueError('sim-extra binary/config hash mismatch; preserve the modified output and rebuild in a new directory')
        sim = a.out.resolve()/f'sim{a.array_size}'
        configs = list(sim.rglob('*.FSAConfig.json'))
        if len(configs) != 1 or not (sim/'simulator').is_file(): raise ValueError('Complete sim for this array first; expected exactly one generated FSAConfig.json')
        env = dict(os.environ, PYTHONPATH=str(ROOT/'generators/easyfloat')+':'+str(ROOT/'generators/fsa/python'))
        subprocess.run([os.environ.get('FSA_PYTHON',sys.executable),str(ROOT/'scripts/ict/a70_verify/verify_sim.py'),'--source',str(ROOT),'--binary',str(sim/'simulator'),'--config',str(configs[0]),'--out',str(a.result_out.resolve()),'--seq',str(a.seq),'--max-cycles',str(a.max_cycles)],cwd=ROOT,env=env,check=True)
    else:
        from ict.board import export, program, test, summarize
        {'export':export,'program':program,'test':test,'summarize':summarize}[a.command](a,p,ROOT)

if __name__ == '__main__':
    try: main()
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print('ERROR:',exc,file=sys.stderr); sys.exit(2)
