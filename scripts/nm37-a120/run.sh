#!/usr/bin/env bash
# All generated files live in a fresh caller-selected directory.
set -eEuo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
export A120_OUT=${A120_OUT:?Set A120_OUT to a fresh absolute output directory}
[[ "$A120_OUT" = /* && "$A120_OUT" != *' '* && "$ROOT" != *' '* ]] || { echo 'Absolute paths without spaces required' >&2; exit 2; }
export USE_CHISEL6=1
# Chisel's resolver otherwise downloads its own firtool version, independent
# of the binary used by the board Makefile and recorded in environment.json.
if command -v firtool >/dev/null 2>&1; then
  export CHISEL_FIRTOOL_PATH=$(dirname "$(command -v firtool)")
fi
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -Xmx16G -Xss8M -XX:ActiveProcessorCount=16 -Dfsa.pePipeline=true -Dfsa.fanoutSplit=false -Dfsa.pipelineConservative=false -Dfsa.nm37MHz=120"
helper="$ROOT/scripts/nm37-a120"
jar="$A120_OUT/generator.jar"
name=chipyard.fpga.nm37.NM37FPGATestHarness.EmptyNM37Config
build="$A120_OUT/A120/fpga/$name"
phase=${1:-help}
trap 'rc=$?; echo "ERROR: phase=$phase exit=$rc line=$LINENO. Input verification PASS is not stage completion." >&2; echo "Preserve logs/artifacts under $A120_OUT. Diagnose the named log; retry in a new output attempt with the same dependency caches. Do not hand-write passed.json." >&2' ERR
case "$phase" in
  help) echo 'Phases: check prepare units formal hbm-startup sim elaborate implement physical bitstream reaudit reaudit-accept reaudit-verify bitstream-from-reaudit'; exit 0;;
  check) python3 "$helper/check.py" sources; exit;;
  physical)
    python3 "$helper/check.py" gate
    python3 "$helper/check.py" physical
    ;;
  reaudit)
    python3 "$helper/reaudit.py" run --source "$ROOT" --build "$A120_OUT" \
      --out "${A120_REAUDIT_OUT:?Set a new A120_REAUDIT_OUT outside the original build/source}"
    ;;
  reaudit-accept)
    python3 "$helper/reaudit.py" accept --out "${A120_REAUDIT_OUT:?Set A120_REAUDIT_OUT}" \
      --attempt "${A120_REAUDIT_ATTEMPT:?Set a new acceptance attempt name}"
    ;;
  reaudit-verify)
    python3 "$helper/reaudit.py" verify --out "${A120_REAUDIT_OUT:?Set A120_REAUDIT_OUT}" \
      --acceptance "${A120_REAUDIT_PASS:?Set the exact revised acceptance path}"
    ;;
  bitstream-from-reaudit)
    python3 "$helper/reaudit.py" bitstream-from-reaudit \
      --out "${A120_REAUDIT_OUT:?Set A120_REAUDIT_OUT}" \
      --acceptance "${A120_REAUDIT_PASS:?Set the exact revised acceptance path}" \
      --destination "${A120_BITSTREAM_OUT:?Set a new bitstream export directory}"
    ;;
  prepare)
    [[ ! -e "$A120_OUT" ]] || { echo 'Refusing to reuse output directory' >&2; exit 2; }
    [[ ! -d "$ROOT/nm37-m1-pipeline" ]] || { echo "Use a fresh checkout; this workspace contains frozen experiment artifacts" >&2; exit 2; }
    python3 "$helper/check.py" sources
    mkdir -p "$A120_OUT/logs"
    # Snapshot the already-vendored, source-verified shell inputs.
    python3 - "$ROOT" "$A120_OUT" <<'PYSHELL'
import json, shutil, sys
from pathlib import Path
root, out = map(Path, sys.argv[1:])
lock = json.loads((root / 'fpga/baselines/nm37-a120/source-lock.json').read_text())
for name in lock['shell_hashes']:
    target = out / 'shell' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / 'fpga/fpga-shells' / name, target)
PYSHELL
    for tool in java firtool verilator vivado; do command -v "$tool"; done
    { java -version; firtool --version; verilator --version; vivado -version; } > "$A120_OUT/logs/tools.txt" 2>&1
    python3 - "$A120_OUT/logs/tools.txt" <<'PYTOOLS'
import sys
from pathlib import Path
versions = Path(sys.argv[1]).read_text()
for expected in ['2020.2_AR75986', '20.0.2', 'firtool-1.75.0', 'Verilator 5.022']:
    if expected not in versions:
        raise SystemExit('Baseline tool version missing: ' + expected)
PYTOOLS
    python3 "$helper/environment.py"
    # Use a stable disposable assembly target and copy out: sbt may delete its
    # previous output when assemblyOutputPath changes. Use a fresh checkout.
    make -C "$ROOT/fpga" SUB_PROJECT=nm37 CONFIG=EmptyNM37Config \
      GENERATOR_CLASSPATH="$ROOT/.classpath_cache/nm37-a120-assembly.jar" \
      "$ROOT/.classpath_cache/nm37-a120-assembly.jar" > "$A120_OUT/logs/assembly.log" 2>&1
    cp "$ROOT/.classpath_cache/nm37-a120-assembly.jar" "$jar"
    python3 "$helper/check.py" record
    ;;
  units)
    python3 "$helper/check.py" run
    [[ ! -e "$A120_OUT/logs/unit.log" ]] || { echo 'Unit log already exists'; exit 2; }
    cd "$ROOT"
    java -jar scripts/sbt-launch.jar -Dsbt.supershell=false \
      "fsa/Test/runMain fsa.PipelineVerification" \
      "fsa/Test/runMain fsa.PipelineVerification emit $A120_OUT/formal" \
      "fsa/Test/runMain fsa.PipelinedScheduleVerification $A120_OUT/score-events.json" \
      "fsa/testOnly fsa.ControlSignalTest -- -z row -z overlapped -z consecutive" \
      > "$A120_OUT/logs/unit.log" 2>&1
    python3 "$helper/check.py" seal units
    ;;
  formal)
    python3 "$helper/check.py" run
    [[ ! -e "$A120_OUT/formal/results.json" ]] || { echo 'Formal results already exist'; exit 2; }
    python3 "$helper/verify_equivalence.py"
    python3 "$helper/check.py" seal formal
    ;;
  hbm-startup)
    python3 "$helper/check.py" run
    [[ ! -e "$A120_OUT/hbm-startup" ]] || { echo 'HBM startup output already exists'; exit 2; }
    mkdir -p "$A120_OUT/hbm-startup"
    cd "$ROOT"
    java -jar scripts/sbt-launch.jar -Dsbt.supershell=false \
      "chipyard_fpga/Test/runMain chipyard.fpga.u280.HBMStartupVerification $A120_OUT/hbm-startup/rtl" \
      > "$A120_OUT/hbm-startup/emission.log" 2>&1
    python3 "$helper/verify_hbm_startup.py" --rtl "$A120_OUT/hbm-startup/rtl" --out "$A120_OUT/hbm-startup"
    python3 "$helper/check.py" seal hbm-startup
    ;;
  sim)
    python3 "$helper/check.py" run
    size=${2:?Expected array size 4, 8, or 16}
    case "$size" in 4|8|16) ;; *) echo "ERROR: --array-size must be 4, 8 or 16 (PE array dimensions, not sequence length); got $size" >&2; exit 2;; esac
    out="$A120_OUT/sim$size"
    [[ ! -e "$out" ]] || { echo 'Simulation output already exists'; exit 2; }
    mkdir -p "$out"
    cfg="AXI4FSA${size}X${size}Fp16Config"
    make -C "$ROOT/sims/verilator" -j"${A120_JOBS:-8}" CONFIG="$cfg" \
      CXX="${CXX:-g++}" CC="${CC:-gcc}" LINK="${CXX:-g++}" \
      GENERATOR_CLASSPATH="$jar" -o "$jar" \
      build_dir="$out/generated-src/chipyard.harness.TestHarness.$cfg" \
      sim="$out/simulator" default > "$out/build.log" 2>&1
    for seq in "$size" "$((size * 2))"; do
      mkdir "$out/seq$seq"
      "${FSA_PYTHON:-$ROOT/generators/fsa/python/.venv/bin/python}" "$helper/verify_sim.py" \
        --binary "$out/simulator" --seq "$seq" --out "$out/seq$seq" \
        --config "$out/generated-src/chipyard.harness.TestHarness.$cfg/chipyard.harness.TestHarness.$cfg.FSAConfig.json" \
        > "$out/seq$seq/test.log" 2>&1
    done
    python3 "$helper/check.py" seal "sim$size"
    ;;
  elaborate)
    python3 "$helper/check.py" run
    [[ ! -e "$A120_OUT/A120" ]] || { echo 'Elaboration already exists'; exit 2; }
    mkdir -p "$A120_OUT/A120"
    make -C "$ROOT/fpga" SUB_PROJECT=nm37 CONFIG=EmptyNM37Config \
      GENERATOR_CLASSPATH="$jar" -o "$jar" build_dir="$build" \
      "$build/$name.vsrcs.f" > "$A120_OUT/A120/elaboration.log" 2>&1
    python3 "$helper/check.py" seal elaborate
    ;;
  implement)
    python3 "$helper/check.py" gate
    [[ ! -e "$build/obj" ]] || { echo 'Implementation already exists'; exit 2; }
    cd "$build"
    mapfile -t ip_scripts < <(find "$build" -name '*.vivado.tcl' | sort)
    vivado -mode batch -source "$helper/implement.tcl" \
      -tclargs -top-module NM37FPGATestHarness -F "$build/$name.vsrcs.f" \
      -board nm37 -ip-vivado-tcls "${ip_scripts[*]}" > "$A120_OUT/A120/implementation.log" 2>&1
    python3 "$helper/check.py" physical
    ;;
  bitstream)
    python3 "$helper/check.py" gate
    python3 "$helper/check.py" physical
    vivado -mode batch -source "$ROOT/fpga/scripts/m1_a120_bitstream.tcl" \
      -tclargs "$build/obj/post_route.dcp" "$A120_OUT/bitstream" > "$A120_OUT/logs/bitstream.log" 2>&1
    ;;
  *) echo "Unknown phase: $phase" >&2; exit 2;;
esac
