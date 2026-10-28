import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ict_cli as cli
from ict.board import validate_receipt, load_export, summarize, routed_inputs


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'source';self.root.mkdir()
        (self.root/'profiles').mkdir()
        self.profile={'schema_version':1,'id':'A70-P3','board':'NM37','dut_mhz':70,'array_sizes':[4,16],'default_array_size':16,
                      'driver':{'output_env':'ICT_BUILD_OUT','commands':{'build':[[sys.executable,'-c','pass']],'sim':[[sys.executable,'-c','pass']],'elaborate':[[sys.executable,'-c','pass']],'implement':[[sys.executable,'-c','pass']]}}}
        (self.root/'profiles/current.json').write_text(json.dumps(self.profile))
        for args in (['init','-q'],['add','.'],['-c','user.name=test','-c','user.email=test@example.invalid','commit','-qm','fixture']):subprocess.run(['git','-C',str(self.root),*args],check=True)
        self.patch=patch.object(cli,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)
        self.out=self.base/'build'
        self.doctor_patch=patch.object(cli,'doctor',return_value=None);self.doctor_patch.start();self.addCleanup(self.doctor_patch.stop)
    def run_cli(self,*args):
        with contextlib.redirect_stdout(io.StringIO()):cli.main(list(args))
    def test_a120_profile_dispatch_and_output_environment(self):
        real = json.loads((Path(__file__).resolve().parents[1]/'profiles/current.json').read_text())
        self.assertEqual((real['id'], real['dut_mhz'], real['apb_mhz']), ('A120-APB60', 120, 60))
        with patch.object(cli, 'profile', return_value=real):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                cli.main(['verify', '--out', str(self.out), '--dry-run'])
            plan = json.loads(stream.getvalue())
            self.assertEqual([c[-1] for c in plan['commands']], ['units', 'formal', 'hbm-startup'])
            self.assertTrue(all(c[1] == 'scripts/nm37-a120/run.sh' for c in plan['commands']))
            self.assertFalse(cli.state_path(self.out).exists())
        p = {**real, 'driver': {'output_env': 'A120_OUT', 'commands': {'build': [
            [sys.executable, '-c', "import os; assert os.environ['ICT_DUT_MHZ']=='120'; assert os.environ['A120_OUT']==os.environ['ICT_BUILD_OUT']"]]}}}
        with patch.object(cli, 'profile', return_value=p):
            self.run_cli('build', '--out', str(self.out))
        self.assertEqual(json.loads((cli.state_path(self.out)/'build.json').read_text())['status'], 'completed')

    def test_dryrun_does_not_create_output(self):
        self.run_cli('build','--out',str(self.out),'--dry-run')
        self.assertFalse(self.out.exists());self.assertFalse(cli.state_path(self.out).exists())
    def test_array1024_is_rejected_before_state(self):
        with self.assertRaisesRegex(ValueError,'Unsupported PE array'):self.run_cli('sim','--out',str(self.out),'--array-size','1024')
        self.assertFalse(cli.state_path(self.out).exists())
    def test_missing_prerequisite(self):
        self.run_cli('build','--out',str(self.out))
        with self.assertRaisesRegex(ValueError,'elaborate'):self.run_cli('implement','--out',str(self.out))
        self.assertFalse((cli.state_path(self.out)/'implement.json').exists())
    def test_completed_stage_does_not_overwrite(self):
        self.run_cli('build','--out',str(self.out));f=cli.state_path(self.out)/'build.json';before=f.read_bytes()
        with self.assertRaisesRegex(ValueError,'already has status=completed'):self.run_cli('build','--out',str(self.out))
        self.assertEqual(before,f.read_bytes())
    def test_failed_stage_records_and_preserves(self):
        with patch.object(cli,'profile',return_value={**self.profile,'driver':{'output_env':'ICT_BUILD_OUT','commands':{'build':[[sys.executable,'-c','raise SystemExit(7)']]}}}):
            with self.assertRaisesRegex(RuntimeError,'exit=7'):self.run_cli('build','--out',str(self.out))
        record=json.loads((cli.state_path(self.out)/'build.json').read_text());self.assertEqual(record['status'],'failed_or_interrupted')
    def test_dirty_source_rejected(self):
        (self.root/'profiles/current.json').write_text(json.dumps(self.profile)+'\n')
        with self.assertRaisesRegex(ValueError,'changes detected'):self.run_cli('build','--out',str(self.out))
    def test_ignored_untracked_scala_rejected(self):
        (self.root/'.git/info/exclude').write_text('*.scala\n')
        extra=self.root/'generators/fsa/src/main/scala/Extra.scala'
        extra.parent.mkdir(parents=True);extra.write_text('object Extra {}')
        with self.assertRaisesRegex(ValueError,'Untracked build source'):self.run_cli('build','--out',str(self.out))
        self.assertFalse(cli.state_path(self.out).exists())
    def test_output_inside_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside source'):self.run_cli('build','--out',str(self.root/'build'))
    def test_sim_extra_requires_completed_and_unchanged_binary(self):
        self.run_cli('build','--out',str(self.out))
        sim=self.out/'sim16';sim.mkdir(parents=True)
        binary=sim/'simulator';binary.write_bytes(b'binary')
        config=sim/'fixture.FSAConfig.json';config.write_text('{}')
        args=['sim-extra','--out',str(self.out),'--array-size','16','--seq','1024','--result-out',str(self.base/'extra')]
        with self.assertRaisesRegex(ValueError,'Complete sim'):self.run_cli(*args)
        record=cli.state_path(self.out)/'sim16.json'
        cli.save(record,{'status':'failed_or_interrupted'})
        with self.assertRaisesRegex(ValueError,'completed sim'):self.run_cli(*args)
        cli.save(record,{'status':'completed','artifacts':{str(binary.relative_to(self.out)):cli.sha(binary),str(config.relative_to(self.out)):cli.sha(config)}})
        binary.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.run_cli(*args)
        self.assertFalse((self.base/'extra').exists())
    def test_receipt_profile_and_hash_required(self):
        receipt=self.base/'receipt.json';manifest={'profile':'A100','bitstream':{'sha256':'a'*64}}
        cli.save(receipt,{'status':'programmed','profile':'A70-P3','bitstream_sha256':'a'*64,'bdf_operator_mapping':'0000:18:00.0'})
        with self.assertRaisesRegex(ValueError,'does not match'):validate_receipt(receipt,manifest,'0000:18:00.0')
        cli.save(receipt,{'status':'programmed','profile':'A100','bitstream_sha256':'a'*64,'bdf_operator_mapping':'0000:18:00.0'})
        self.assertEqual(validate_receipt(receipt,manifest,'0000:18:00.0')['profile'],'A100')
        with self.assertRaisesRegex(ValueError,'PCI BDF differs'):validate_receipt(receipt,manifest,'0000:19:00.0')
    def test_export_routed_hash_binding_even_after_cdc_failure(self):
        self.run_cli('build','--out',str(self.out))
        obj=self.out/'A70/fpga/design/obj';obj.mkdir(parents=True)
        dcp=obj/'post_route.dcp';dcp.write_bytes(b'routed')
        config=obj.parent/'design.FSAConfig.json';config.write_text('{}')
        state=cli.state_path(self.out)
        with self.assertRaisesRegex(ValueError,'No implementation attempt'):routed_inputs(self.out,state)
        cli.save(state/'implement.json',{'status':'failed_or_interrupted','error':'CDC review pending','routed_artifacts':{str(f.relative_to(self.out)):cli.sha(f) for f in [dcp,config]}})
        self.assertEqual(routed_inputs(self.out,state),(dcp,config))
        config.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError,'changed after implementation'):routed_inputs(self.out,state)
    def test_export_files_hash_checked(self):
        exp=self.base/'export';exp.mkdir();(exp/'image.bit').write_bytes(b'bit');(exp/'config.json').write_text('{}')
        m={'status':'exported','profile':'A70-P3','clock_mhz':70,'bitstream':{'path':'image.bit','sha256':cli.sha(exp/'image.bit')},'config':{'path':'config.json','sha256':cli.sha(exp/'config.json')}}
        cli.save(exp/'experiment.json',m);load_export(exp,self.profile)
        (exp/'image.bit').write_bytes(b'different')
        with self.assertRaisesRegex(ValueError,'hash/path mismatch'):load_export(exp,self.profile)
    def test_extra_sequence_wrong_command_explained(self):
        with self.assertRaisesRegex(ValueError,'sim-extra'):self.run_cli('sim','--out',str(self.out),'--seq','1024')

if __name__=='__main__':unittest.main()
