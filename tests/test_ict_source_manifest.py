"""Exercise the maintainer entry on isolated Git inputs, without FPGA tools."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class SourceManifestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.shell = self.root / 'fpga/fpga-shells'
        self.shell.mkdir(parents=True)
        (self.shell / 'xilinx').mkdir()
        scripts = self.root / 'scripts'
        scripts.mkdir()
        shutil.copy2(REPO / 'scripts/ict-source-manifest.py', scripts)
        for short in ('a100', 'a110'):
            dest = scripts / ('nm37-' + short)
            dest.mkdir()
            shutil.copy2(REPO / 'scripts' / dest.name / 'check.py', dest)
            lock = self.root / 'fpga/baselines' / dest.name / 'source-lock.json'
            lock.parent.mkdir(parents=True)
            lock.write_text(json.dumps({'source_modes': {}, 'source_hashes': {},
                                        'shell_hashes': {'xilinx/board.xdc': 'stale'}}))
        (self.shell / 'xilinx/board.xdc').write_text('set example 1\n')
        self.git('init', '-q')
        self.git('add', '.')

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def refresh(self, profile, write=True, success=True):
        cmd = [sys.executable, str(self.root / 'scripts/ict-source-manifest.py'),
               '--profile', profile]
        if write:
            cmd.append('--write')
        p = subprocess.run(cmd, text=True, capture_output=True)
        self.assertEqual(p.returncode == 0, success, p.stdout + p.stderr)
        return p

    def lock(self, profile):
        short = 'a100' if profile == 'A100' else 'a110'
        return self.root / f'fpga/baselines/nm37-{short}/source-lock.json'

    def test_content_change_updates_both_locks_and_check_does_not_write(self):
        for profile in ('A100', 'A110-APB55'):
            with self.subTest(profile=profile):
                self.refresh(profile)
                path = self.lock(profile)
                before = path.read_bytes()
                data = (self.shell / 'xilinx/board.xdc').read_bytes() + b'# reviewed change\n'
                (self.shell / 'xilinx/board.xdc').write_bytes(data)
                self.git('add', 'fpga/fpga-shells')
                self.refresh(profile, write=False, success=False)
                self.assertEqual(path.read_bytes(), before)
                self.refresh(profile)
                lock = json.loads(path.read_text())
                wanted = hashlib.sha256(data).hexdigest()
                self.assertEqual(lock['source_hashes']['fpga/fpga-shells/xilinx/board.xdc'], wanted)
                self.assertEqual(lock['shell_hashes']['xilinx/board.xdc'], wanted)
                self.refresh(profile, write=False)

    def test_tracked_add_remove_and_symlink_snapshot_membership(self):
        self.refresh('A110-APB55')
        self.git('rm', '--cached', 'fpga/fpga-shells/xilinx/board.xdc')
        (self.shell / 'xilinx/board.xdc').unlink()
        (self.shell / 'xilinx/new.tcl').write_text('set replacement 1\n')
        # Non-runtime shell inputs are locked as source, not copied to OUT/shell.
        (self.shell / 'source-link').symlink_to('xilinx/new.tcl')
        self.git('add', 'fpga/fpga-shells')
        (self.shell / 'xilinx/untracked.xdc').write_text('# not reviewed/staged\n')
        self.refresh('A110-APB55')
        lock = json.loads(self.lock('A110-APB55').read_text())
        self.assertEqual(set(lock['shell_hashes']), {'xilinx/new.tcl'})
        self.assertEqual(lock['source_hashes']['fpga/fpga-shells/source-link'], hashlib.sha256(b'xilinx/new.tcl').hexdigest())
        self.assertEqual(lock['source_modes']['fpga/fpga-shells/source-link'], '120000')
        self.assertFalse(list(self.root.rglob('*.passed.json')))

    def test_empty_shell_rejected_without_rewriting_lock(self):
        path = self.lock('A100')
        before = path.read_bytes()
        self.git('rm', '--cached', 'fpga/fpga-shells/xilinx/board.xdc')
        result = self.refresh('A100', success=False)
        self.assertIn('No tracked Xilinx shell inputs', result.stderr)
        self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
