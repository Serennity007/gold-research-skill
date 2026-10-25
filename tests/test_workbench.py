import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import run_research as tool


class ExternalResources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.external=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if tag in ('script','link','img','iframe') and key in ('src','href'):
                self.external.append(value)


class WorkbenchTests(unittest.TestCase):
    def test_bundle_freezes_inputs_and_can_replay_without_original_files(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=tool.run(ROOT/'examples/workbench.json',temp)
            result=json.loads((directory/'bundle.json').read_text(encoding='utf-8'))
            self.assertEqual(json.loads((directory/'COMPLETE.json').read_text())['status'],'complete')
            for role,item in result['inputs'].items():
                self.assertEqual(hashlib.sha256((directory/'inputs'/f'{role}.csv').read_bytes()).hexdigest(),item['sha256'])
            replay=tool.run(directory/'config.snapshot.json',temp)
            second=json.loads((replay/'bundle.json').read_text(encoding='utf-8'))
            self.assertEqual(result['metrics'],second['metrics'])
            self.assertEqual(result['advanced'],second['advanced'])
            self.assertNotEqual(replay,directory)
            self.assertEqual(result['data_kind'],'synthetic')

    def test_cli_runs_outside_repo_and_reports_complete_export(self):
        with tempfile.TemporaryDirectory() as temp:
            process=subprocess.run([sys.executable,str(ROOT/'scripts/run_research.py'),'--config',str(ROOT/'examples/workbench.json'),'--out',str(Path(temp)/'folder with spaces')],cwd=temp,capture_output=True,text=True)
            self.assertEqual(process.returncode,0,process.stderr)
            self.assertIn('PASS',process.stdout)
            folders=list((Path(temp)/'folder with spaces').iterdir())
            self.assertEqual(len(folders),1)
            self.assertTrue((folders[0]/'REPORT.html').is_file())

    def test_imported_sources_missing_metadata_fail_before_output(self):
        config=json.loads((ROOT/'examples/workbench.json').read_text(encoding='utf-8'))
        config['data_kind']='imported_observations'
        config['files']={key:str((ROOT/'examples'/value).resolve()) for key,value in config['files'].items()}
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'config.json'
            path.write_text(json.dumps(config),encoding='utf-8')
            output=Path(temp)/'output'
            with self.assertRaises(ValueError):
                tool.run(path,output)
            self.assertFalse(output.exists())

    def test_stale_bars_and_short_history_remain_visible(self):
        config,raw,_=tool.load(ROOT/'examples/workbench.json')
        config['as_of']='2024-01-15T12:00:00Z'
        result=tool.calculate(config,raw)
        self.assertTrue(any('陈旧' in item for item in result['attention']))
        raw=dict(raw,bars=b'\n'.join(raw['bars'].splitlines()[:3])+b'\n')
        result=tool.calculate(config,raw)
        self.assertTrue(any('历史不足' in item for item in result['attention']))

    def test_html_escapes_user_text_and_has_no_external_assets(self):
        config,raw,result=tool.load(ROOT/'examples/workbench.json')
        config['instrument']='<img src=x onerror=alert(1)>'
        result=tool.calculate(config,raw)
        html=tool.html_report(result,raw)
        parser=ExternalResources()
        parser.feed(html)
        self.assertFalse(parser.external)
        self.assertNotIn('<img src=x',html)
        self.assertIn('&lt;img',html)
