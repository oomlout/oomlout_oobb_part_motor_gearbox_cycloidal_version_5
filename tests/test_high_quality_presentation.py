"""Regression coverage for V4-specific HQ authoring (no CAD process needed)."""
import copy
import importlib
import json
from pathlib import Path
import sys
import unittest

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,json.loads((PROJECT/'solidcraft/config.json').read_text())['helper_root'])
from oobb_solidcraft._loader import load


class Client:
    def __init__(self):self.commands=[]
    def execute(self,command,**params):
        self.commands.append((command,params))
        return {}


class HighQualityPresentationTests(unittest.TestCase):
    def setUp(self):
        self.f=importlib.import_module(load('high_quality_hardware').__name__+'.families')

    def test_m6_thread_uses_matching_designation_and_pick(self):
        spec=copy.deepcopy(self.f.SPECS['bolt_m3_25mm_hex_head'])
        spec['designation']='M6x1'
        spec['parameters'].update(diameter=6,length=40,head_af=10,head_height=4)
        client=Client();self.f.author(client,spec)
        thread=next(p for c,p in client.commands if c=='solid.thread')
        self.assertEqual(thread['designation'],'M6x1')
        self.assertEqual(thread['face'],[3,0,-39])
        self.assertTrue(thread['modeled'])

    def test_bearing_retains_all_balls_and_enclosing_windows(self):
        spec=copy.deepcopy(self.f.SPECS['bearing_608_open'])
        spec.update(ball_count=12,detail={'window_encloses_relief':True})
        client=Client();self.f.author(client,spec)
        spheres=[p for c,p in client.commands if c=='solid.sphere']
        windows=[p for c,p in client.commands if c=='solid.cylinder']
        self.assertEqual(len(spheres),12)
        self.assertTrue(all(p['operation']=='new' for p in spheres))
        self.assertEqual(len(windows),24)

    def test_default_library_keeps_seven_balls_and_reliefs(self):
        client=Client();self.f.author(client,self.f.SPECS['bearing_608_open'])
        spheres=[p for c,p in client.commands if c=='solid.sphere']
        self.assertEqual(sum(p['operation']=='new' for p in spheres),7)
        self.assertEqual(sum(p['operation']=='cut' for p in spheres),14)

    def test_partial_thread_is_an_editable_parameter(self):
        spec=copy.deepcopy(self.f.SPECS['bolt_m3_25mm_hex_head'])
        spec['parameters']['thread_length']=12
        client=Client();self.f.author(client,spec)
        thread=next(p for c,p in client.commands if c=='solid.thread')
        self.assertEqual(thread['length'],'thread_length')
        self.assertIn(('parameters.add',{'name':'thread_length','expression':'12 mm'}),client.commands)

    def test_cannot_omit_relief_if_window_does_not_cover_it(self):
        spec=copy.deepcopy(self.f.SPECS['bearing_608_open'])
        spec['parameters']['ball_radius']=3
        spec['detail']={'window_encloses_relief':True}
        with self.assertRaisesRegex(ValueError,'window does not enclose'):
            self.f.author(Client(),spec)


if __name__=='__main__':unittest.main()
