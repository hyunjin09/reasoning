"""Prepare masked, image-only source/readout nominations for explicit review.

Coordinates below are single-annotator measurements from the source images.
This is a bounded discrete-content assay inventory, not exhaustive annotation
of all objects or of geometric relations. Nothing here opens model features.
"""
import bisect
import json
import re
from pathlib import Path

from scripts.stage8c.prepare import save, sha

ROOT = Path('outputs/stage9a/v1')

# image: [(source identity, printed/visible value, normalized cx,cy,width,height)]
SOURCES = {
 204: [('marked_center','1',.494,.504,.045,.076),('right_neighbor','2',.596,.504,.045,.076),('left_neighbor','1',.384,.504,.045,.076)],
 276: [('upper_left_circle','3',.264,.25,.09,.12),('upper_right_circle','5',.735,.25,.09,.12)],
 475: [('left_lower_left_stone','26',.25,.493,.054,.047),('left_upper_stone','8',.322,.406,.035,.047),('left_lower_right_stone','12',.354,.504,.05,.047),('right_left_stone','20',.655,.444,.05,.047),('right_right_stone','17',.754,.444,.05,.047)],
 566: [('row1_column1','white',.166,.199,.075,.105),('row1_column2','black',.305,.199,.075,.105),('row1_column3','white',.445,.199,.075,.105)],
 651: [('left_high_ladder','32',.211,.106,.105,.061),('right_high_ladder','48',.682,.106,.105,.061),('middle_ladder','36',.494,.281,.105,.061)],
 784: [('top_horizontal_label','5',.204,.14,.064,.13),('upper_step_label','2',.295,.329,.064,.13),('middle_vertical_label','4',.599,.591,.064,.13)],
 867: [('top_circle','7',.507,.137,.075,.085),('upper_left_circle','3',.331,.275,.075,.085),('lower_left_circle','1',.228,.630,.075,.085),('bottom_circle','6',.507,.844,.075,.085),('lower_right_circle','2',.796,.630,.075,.085)],
 885: [('top_first_label','A',.540,.186,.041,.13),('top_second_label','B',.620,.186,.041,.13),('top_third_label','C',.699,.186,.041,.13),('top_right_label','D',.933,.186,.041,.13),('bottom_label','E',.778,.803,.041,.13),('start_label','S',.120,.803,.041,.13)],
 947: [('top_loop','10',.443,.24,.10,.06),('middle_loop','15',.484,.44,.10,.06),('left_loop','12',.323,.645,.10,.06),('right_loop','13',.618,.695,.10,.06)],
 988: [('row1_column1','1',.164,.315,.065,.18),('row1_column2','3',.336,.315,.065,.18),('row1_column3','5',.50,.315,.065,.18),('row1_column4','2',.668,.315,.065,.18),('row1_column5','13',.835,.315,.115,.18),('row2_column1','7',.164,.675,.065,.18),('row2_column2','4',.336,.675,.065,.18),('row2_column3','6',.50,.675,.065,.18),('row2_column4','8',.668,.675,.065,.18),('row2_column5','11',.835,.675,.115,.18)],
 990: [('left_interval','24',.147,.813,.057,.105),('middle_interval','30',.344,.813,.057,.105),('right_interval','66',.696,.813,.057,.105)],
 1080: [('upper_horizontal','11',.150,.164,.045,.075),('lower_horizontal','13',.274,.369,.045,.075)],
 1146: [('top_gap','2',.444,.188,.045,.12),('left_gap','3',.116,.336,.045,.12),('right_gap','4',.83,.472,.045,.12),('bottom_gap','3',.49,.781,.045,.12)],
 1221: [('top_left_area','8',.447,.399,.064,.093),('top_right_area','10',.655,.32,.108,.093),('bottom_left_area','18',.425,.66,.108,.093)],
 1237: [('top_horizontal_product','30',.91,.148,.092,.079),('bottom_left_product','48',.12,.887,.092,.079),('bottom_middle_left_product','105',.367,.887,.12,.079),('bottom_middle_right_product','28',.57,.887,.092,.079),('bottom_right_product','144',.817,.887,.12,.079)],
 1430: [('middle_horizontal_band','white',.62,.515,.10,.10),('top_horizontal_band','gray',.62,.23,.10,.10),('left_vertical_band','dark',.14,.515,.10,.10)],
 1476: [('top_left_corner','P',.164,.12,.075,.10),('top_right_corner','S',.88,.12,.075,.10),('bottom_left_corner','Q',.15,.876,.075,.10),('bottom_right_corner','R',.88,.875,.075,.10),('top_interior_point','V',.344,.117,.075,.10),('middle_junction','W',.536,.575,.09,.10),('bottom_interior_point','T',.344,.884,.075,.10),('right_interior_point','U',.883,.49,.075,.10)],
 1478: [('left_square','P',.147,.675,.055,.125),('right_square','R',.69,.609,.055,.125)],
 1526: [('central_full_face','gray',.502,.308,.035,.045),('upper_full_face','white',.502,.211,.035,.045),('right_full_face','white',.568,.308,.035,.045)],
 1563: [('top_vertex','1',.398,.12,.066,.098),('left_vertex','5',.101,.525,.066,.098)],
 1568: [('left_inner_tick','a',.404,.517,.027,.15),('second_inner_tick','b',.455,.517,.027,.15),('middle_inner_tick','c',.506,.517,.027,.15),('fourth_inner_tick','d',.559,.517,.027,.15),('right_inner_tick','e',.610,.517,.027,.15)],
 1948: [('left_first_number','JK',.35,.493,.23,.145),('left_second_number','LM',.35,.665,.23,.145),('right_first_number','JM',.80,.164,.23,.145),('right_second_number','LM',.80,.332,.23,.145),('right_third_number','JK',.80,.493,.23,.145),('right_fourth_number','LK',.80,.665,.23,.145)],
 2013: [('row1_column1','1',.156,.147,.045,.07),('row1_column2','2',.43,.147,.045,.07),('row2_column1','3',.155,.43,.045,.07),('row2_column3','4',.706,.431,.045,.07),('row3_column2','5',.43,.72,.045,.07)],
 2019: [('apex','C',.604,.137,.055,.085),('left_base','A',.082,.807,.055,.085),('right_base','B',.92,.807,.055,.085),('left_inner_base','M',.392,.866,.07,.085),('right_inner_base','N',.746,.866,.07,.085)],
 2035: [('upper_notch_endpoint','A',.815,.136,.07,.07),('inner_notch_corner','B',.735,.67,.07,.07),('lower_notch_endpoint','C',.932,.67,.07,.07)],
 2143: [('outer_top_left','A',.08,.073,.075,.067),('outer_top_right','B',.926,.073,.075,.067),('outer_bottom_right','C',.926,.926,.075,.067),('outer_bottom_left','D',.08,.926,.075,.067),('inner_top','E',.55,.229,.075,.067),('inner_right','F',.785,.56,.075,.067),('inner_bottom','G',.443,.76,.075,.067),('inner_left','H',.223,.434,.075,.067)],
 2245: [('descending_diagonal','8',.35,.183,.045,.10),('upper_notch_side','1',.817,.13,.045,.10)],
 2284: [('left_base_vertex','A',.042,.923,.028,.04),('top_vertex','B',.23,.06,.028,.04),('right_base_vertex','C',.96,.923,.028,.04)],
 2464: [('left_slanted_side','3',.275,.31,.038,.076),('right_slanted_side','4',.565,.31,.038,.076),('base_side','5',.45,.584,.038,.076)],
 2580: [('left_upper_vertex','A',.094,.445,.068,.10),('top_vertex','B',.493,.117,.068,.10),('right_upper_vertex','C',.917,.549,.068,.10),('left_lower_vertex','E',.09,.867,.068,.10),('right_lower_vertex','D',.91,.882,.068,.10),('left_intersection','F',.334,.61,.068,.10),('right_intersection','G',.683,.658,.068,.10)],
 2701: [('spinner1_top','1',.501,.164,.073,.067),('spinner1_left','5',.309,.324,.073,.067),('spinner1_right','3',.694,.324,.073,.067),('spinner2_top','2',.501,.675,.073,.067),('spinner2_left','6',.309,.835,.073,.067),('spinner2_right','4',.694,.835,.073,.067)],
 2781: [('top_left','A',.235,.082,.043,.058),('top_middle','B',.41,.247,.043,.058),('top_right','C',.633,.247,.043,.058),('rightmost','D',.936,.75,.043,.058),('bottom','E',.774,.923,.043,.058),('bottom_middle_right','F',.631,.702,.043,.058),('bottom_middle_left','G',.409,.702,.043,.058),('leftmost','H',.066,.344,.043,.058),('left_right_angle','J',.278,.568,.043,.058),('right_right_angle','I',.787,.486,.043,.058)],
 2962: [('bottom_base','8',.50,.975,.055,.025),('lower_left_vertical','12',.06,.676,.06,.026),('right_vertical','18',.929,.535,.06,.026),('upper_side','6',.64,.048,.05,.026),('upper_left_slant','8',.193,.190,.05,.026)],
 2981: [('apex','A',.489,.044,.028,.04),('left_base','B',.036,.9,.028,.04),('front_base','C',.54,.963,.028,.04),('right_base','D',.967,.86,.028,.04),('back_base','E',.422,.775,.028,.04)],
}


def main():
    dest = ROOT/'annotations/source_review'
    inventory = {str(k): [dict(source_id=r[0],value=r[1],box=[r[2]-r[4]/2,r[3]-r[5]/2,r[2]+r[4]/2,r[3]+r[5]/2]) for r in rs] for k,rs in SOURCES.items()}
    save(dest/'inventory_proposed.json', dict(images=inventory,reviewer='Codex main agent',
        scope='Discrete printed values/letters or uniform region color with existing different-content donor; relation-only/whole-object structural edits outside this bounded replay implementation.'))
    semantic=json.loads((ROOT/'annotations/semantic_review_complete.json').read_text())
    events=json.loads((ROOT/'annotations/review_work/masked_events.json').read_text())
    accepted={r['review_index'] for r in semantic['rows'] if r['semantic_label']=='accepted'}
    index={r['packet_id']:r for r in json.loads((ROOT/'annotations/packet_index.json').read_text())['rows']}
    candidates=[];cached={}
    for event in events:
        if event['review_index'] not in accepted:continue
        item=Path(event['image']).stem
        if item not in inventory:continue
        p=event['packet_id']
        if p not in cached:
            d=Path(index[p]['receipt']).parent
            tokens=[json.loads(line) for line in (d/'tokens.jsonl').read_text().splitlines()]
            pieces=[t['decoded_token'] for t in tokens];offsets=[0]
            for piece in pieces:offsets.append(offsets[-1]+len(piece))
            cached[p]=(tokens,''.join(pieces),offsets)
        tokens,text,offsets=cached[p]
        lo=offsets[event['demand_token']];hi=offsets[min(event['excerpt_end'],event['demand_token']+256)]
        for value in dict.fromkeys(r['value'] for r in inventory[item]):
            if len(value)==2 and value.isalpha() and value.isupper():
                pattern=r'(?<![A-Za-z])'+r'\s*'.join(value)+r'(?![A-Za-z])'
            elif value=='gray':pattern=r'\bgr[ae]y\b'
            elif value.isdigit():pattern=r'(?<![\d.])'+value+r'(?![\d.])'
            else:pattern=r'\b'+re.escape(value)+r'\b'
            match=re.search(pattern,text[lo:hi])
            if not match:continue
            a=lo+match.start();b=lo+match.end()
            t0=bisect.bisect_right(offsets,a)-1;t1=bisect.bisect_left(offsets,b)
            if t0==0:continue
            candidates.append(dict(candidate_index=len(candidates),review_index=event['review_index'],
                packet_id=p,event_id=event['event_id'],item_id=item,demand_token=event['demand_token'],
                value=value,readout_start=t0,readout_end=t1,character_span=[a,b],
                readout_text=text[offsets[t0]:offsets[t1]],value_offset_in_readout=[a-offsets[t0],b-offsets[t0]],
                source_options=[r['source_id'] for r in inventory[item] if r['value']==value],
                context=text[max(lo,a-180):min(hi,b+150)],
                next='Explicitly accept unique source binding or reject; donor/irrelevant geometry then frozen before scoring.'))
    save(dest/'candidates.json',dict(rows=candidates,semantic_sha256=sha(ROOT/'annotations/semantic_review_complete.json'),
        inventory_sha256=sha(dest/'inventory_proposed.json'),selection_used_outcomes=False))
    print(json.dumps(dict(candidate_count=len(candidates),events=len({r['event_id'] for r in candidates}),images=len({r['item_id'] for r in candidates}))))


if __name__=='__main__':main()
