#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
verilator --cc --exe --build -j 4 --top-module ResetWrangler -Wno-fatal -DSYNTHESIS --Mdir obj_test ResetWrangler.sv AsyncResetRegVec_w14_i0.sv AsyncResetReg.sv ResetCatchAndSync_d3.sv AsyncResetSynchronizerShiftReg_w1_d3_i0.sv AsyncResetSynchronizerPrimitiveShiftReg_d3_i0.sv reset_test.cpp > test-build.log 2>&1
./obj_test/VResetWrangler > test-result.txt 2>&1
cat test-result.txt
