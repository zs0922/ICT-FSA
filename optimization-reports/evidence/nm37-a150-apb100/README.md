# A150/APB100 acceptance evidence

physical.passed.json is the final acceptance after scoped CDC review. build01.exit remains 1 from the original pending-review run.
Hardware source: 32480c2630fea1073c7666ea0e4c2f75a49ac358. No hardware reimplementation in this review.
physical-reports/*.gz are original report bytes compressed with gzip; decompress before checking hashes against physical.passed.json.
cdc-review.json evidence paths are relative to original build01; cdc-evidence/ is copied with identical bytes.
The 241 MiB routed DCP and simulator executables remain in the external build tree; their hashes/stage seals are recorded, not embedded in Git.
Audit tests require Python 3.14 for the frozen AST serialization fingerprint. Other Python-version failure logs are retained.
Bitstream exported subsequently from the same accepted DCP; see bitstream-export/. No board test or push. See ../../NM37_A150_APB100.md for acceptance limits and reproduction commands.
