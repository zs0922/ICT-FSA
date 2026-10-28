export FSA_A120_BASE=/home/zhangsi/tmp/FSA-m1/nm37-a120-20261023
export FSA_A120_WORK=$FSA_A120_BASE/src
export A120_OUT=$FSA_A120_BASE/c0-build02
export RISCV=/home/zhangsi/riscv
export PATH=/opt/Xilinx_2020.2/Vivado/2020.2/bin:/home/zhangsi/tmp/FSA-m1/.conda-env/bin:/home/zhangsi/.local/bin:/home/zhangsi/circt/bin:$RISCV/bin:$PATH
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export A120_JOBS=16
export FSA_PYTHON=/home/zhangsi/tmp/FSA-m1/generators/fsa/python/.venv/bin/python
export PYTHONPATH=$FSA_A120_WORK/generators/easyfloat
export YOSYS=/home/zhangsi/tmp/FSA-m1/nm37-m1-shiftjam/formal-env/bin/yowasp-yosys
# Download/compiler bootstrap caches only; no generated JAR, RTL or simulator is reused.
export COURSIER_CACHE=/home/zhangsi/tmp/FSA-m1/nm37-m1-pipeline/apb110-20261020/coursier/v1
export XDG_CACHE_HOME=$FSA_A120_BASE/xdg-cache
export XDG_RUNTIME_DIR=/tmp/fsa-a120-runtime
export JAVA_TOOL_OPTIONS="-Dsbt.ivy.home=/home/zhangsi/tmp/FSA-m1/nm37-m1-pipeline/apb110-20261020/src/.ivy2 -Dsbt.global.base=/home/zhangsi/tmp/FSA-m1/nm37-m1-pipeline/apb110-20261020/src/.sbt -Dsbt.boot.directory=/home/zhangsi/tmp/FSA-m1/nm37-m1-pipeline/apb110-20261020/src/.sbt/boot -Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false"
