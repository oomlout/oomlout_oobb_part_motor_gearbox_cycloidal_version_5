"""Read-only inventory, registration and axial-fastener audit of this presentation."""
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np

P=Path(__file__).resolve().parents[1]
ROOT=P.parent


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def audit(data):
    operation=data['operation']
    assert operation['ring_contacts']==data['geometry']['ring_count']==20
    assert operation['disc_lobes']==operation['ring_contacts']-1==19
    assert operation['nominal_reduction']==operation['disc_lobes']==19
    models=np.load(P/'raw/studio.npz')
    names={n[:-2] for n in models.files if n.endswith('_v') and not n.startswith('rounded_')}
    hardware={n for n in names if n.startswith('hardware_')}
    printed=names-hardware
    scenes=read(P/'raw/scenes.json')
    assert set(scenes['square']['bodies'])==names
    assert set(scenes['printed']['bodies'])==printed
    assert all(z==0 for z in scenes['square']['bodies'].values())
    assert len(printed)==data['geometry']['printed_count']==46
    assert len(hardware)==data['geometry']['hardware_mesh_body_count']==124
    matched=set()
    for p in data['printed_parts']:
        selected={n for n in printed if re.search(p['scene_pattern'],n)}
        assert len(selected)==p['quantity'],(p['ref'],selected)
        assert not selected & matched
        matched |= selected
    assert matched==printed
    hardware_counts={}
    for p in data['hardware']:
        selected={n for n in hardware if re.search(p['scene_pattern'],n)}
        assert len(selected)==p['quantity'],(p['ref'],len(selected),p['quantity'])
        hardware_counts[p['ref']]=len(selected)
    assert sum(hardware_counts.values())==data['geometry']['hardware_piece_count']==98
    # Socket-cap heads and shanks are separate bodies representing one screw.
    extra_heads={n for n in hardware if n.startswith(('hardware_ring_cap_heads','hardware_drive_caps'))}
    assert len(extra_heads)==26
    expected=read(P/'source/cad/assembled_health.json')['bodies']
    max_error=0
    for body in expected:
        n=body['name']
        if n not in names:continue
        vertices=models[n+'_v']
        box=np.array([vertices.min(axis=0),vertices.max(axis=0)])
        reference=np.array([body['bbox']['min'],body['bbox']['max']])
        error=float(np.abs(box-reference).max())
        assert error<.08,(n,error)
        max_error=max(max_error,error)

    def bbox(n):
        v=models[n+'_v'];return np.array([v.min(axis=0),v.max(axis=0)])
    def family(prefix):return sorted(n for n in hardware|printed if n==prefix or n.startswith(prefix+' ('))
    axes={}
    for sleeves,shanks,heads in [('printed_contact_sleeve','hardware_ring_M3_shanks','hardware_ring_cap_heads'),
                                 ('printed_drive_sleeve','hardware_drive_shanks','hardware_drive_caps')]:
        locations=[bbox(n).mean(axis=0)[:2] for n in family(sleeves)]
        errors=[min(float(np.linalg.norm(bbox(n).mean(axis=0)[:2]-xy)) for xy in locations)
                for prefix in (shanks,heads) for n in family(prefix)]
        assert max(errors)<.01
        axes[sleeves]={'count':len(locations),'maximum_axis_error_mm':max(errors)}
    engagement={}
    pairs=[('ring','hardware_ring_M3_shanks','hardware_M3_ring_nuts'),
           ('guide','hardware_drive_shanks','hardware_drive_nuts'),
           ('shaft_lower','hardware_shaft_M3x35_lower','hardware_shaft_tie_nut_lower'),
           ('shaft_upper','hardware_shaft_M3x35_upper','hardware_shaft_tie_nut_upper'),
           ('disc_a','hardware_disc_a_M3x6_1','hardware_disc_a_nut_1'),
           ('disc_b','hardware_disc_b_M3x6_1','hardware_disc_b_nut_1')]
    for label,screw,nut in pairs:
        a,b=bbox(screw),bbox(nut)
        overlap=float(min(a[1,2],b[1,2])-max(a[0,2],b[0,2]))
        assert overlap>=1.74,(label,overlap)
        engagement[label]=overlap
    start=scenes['layer_start']['bodies']
    assert 'temporary_shaft_tie' in start and 'hardware_shaft_M3x35_lower' not in start
    assert 'hardware_shaft_tie_nut_upper' not in start
    end=scenes['layer_end']['bodies']
    assert set(end)==names and 'temporary_shaft_tie' not in end
    assert len([n for n in start if n.startswith('hardware_ring_M3_shanks')])==20
    assert len([n for n in start if n.startswith('hardware_drive_shanks')])==6
    for key,carrier,endname in [('layer_inner','top','upper'),('layer_finish_inner','bottom','lower')]:
        layer=scenes[key]['bodies']
        assert sum(n.startswith('hardware_carrier_'+carrier+'_mount_nut') for n in layer)==8
        assert sum(n.startswith('hardware_shaft_mount_nut_'+endname) for n in layer)==4
    report={'status':'PASS','master_sha256':data['source']['master_sha256'],'printed_pieces':len(printed),
            'hardware_pieces':sum(hardware_counts.values()),'hardware_reference_mesh_bodies':len(hardware),
            'hardware_by_reference':hardware_counts,'registration_max_error_mm':max_error,
            'sleeve_screw_axes':axes,'nominal_axial_screw_nut_overlap_mm':engagement,
            'standing_screws':28,'temporary_screw_reversal':'checked in scene inventory',
            'mechanical_evidence':['layered_assembly_verification.json','assembly_sequence_verification.json','fit_verification.json'],
            'scope':'Read-only digital consistency and nominal geometry; no new physical fit or load result.'}
    (P/'qa/geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report


if __name__=='__main__':
    print(json.dumps(audit(read(P/'project.json')),indent=2))
