import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from ict import board

class U280Recovery(unittest.TestCase):
    def test_exact_sta_period_and_wrong_clock(self):
        # Exercise the exact Tcl condition used by export; no slack waiver.
        script=(ROOT/'scripts/ict/export.tcl').read_text()
        condition=script.split('if {[llength $dut] != 1 || ',1)[1].split('} {',1)[0]
        for actual, expected_result in [('14.284','0'),('10.000','1'),('14.286','1')]:
            tcl='proc get_property {name obj} {return '+actual+'}\nset dut dut\nset expected_period 14.284285714285715\nputs [expr {'+condition+'}]\n'
            p=subprocess.run(['tclsh'],input=tcl,text=True,capture_output=True,check=True)
            self.assertEqual(p.stdout.strip(),expected_result)

    def test_recovery_binds_original_profile_and_rejects_hardware_changes(self):
        p=json.loads((ROOT/'profiles/current.json').read_text())
        old=copy.deepcopy(p);old.pop('sta_dut_period_ns')
        old_text=json.dumps(old,indent=2)+'\n'; commit='a'*40
        with tempfile.TemporaryDirectory() as d:
            state=Path(d); (state/'source.json').write_text(json.dumps({'commit':commit,'profile':'U280','profile_sha256':hashlib.sha256(old_text.encode()).hexdigest()}))
            changes=['scripts/ict/export.tcl']
            def git(*args):
                if args[0]=='merge-base':return commit
                if args[0]=='show':return old_text.strip()
                if args[0]=='diff':return '\n'.join(changes)
                self.fail(args)
            with patch.object(board,'source_identity'),patch.object(board,'state_path',return_value=state),patch.object(board,'git',side_effect=git):
                self.assertEqual(board.recovery_binding(Path('/not-used'),p,commit)[0],state)
                changes.append('generators/fsa/src/main/scala/fsa/PE.scala')
                with self.assertRaisesRegex(ValueError,'non-audit changes'):
                    board.recovery_binding(Path('/not-used'),p,commit)
                changes.pop(); bad=copy.deepcopy(p);bad['dut_mhz']=100
                with self.assertRaisesRegex(ValueError,'only the documented'):
                    board.recovery_binding(Path('/not-used'),bad,commit)
                with self.assertRaisesRegex(ValueError,'does not match'):
                    board.recovery_binding(Path('/not-used'),p,'b'*40)

if __name__=='__main__':unittest.main()
