"""Human-readable illustrations; no new scoring or modification of sealed labels."""
import json
from pathlib import Path

from scripts.thinking_math_failure_audit.analyze import ROOT, OUT, read_rows, read_json, save_json, sha


def main():
    rows={r['task_id']:r for r in read_rows(ROOT/'outputs/stage14b/scoring/scored_outputs.jsonl') if r['model']=='T'}
    screens={r['task_id']:r for r in read_rows(OUT/'trace_screens.jsonl')}
    s=(ROOT/'outputs/stage14d0/viewer/data.js').read_text()
    audited={c['item_id']:c for c in json.loads(s[s.index('{'):].rstrip().removesuffix(';'))['cases']}
    family_notes={r['problem_index']:r['review_note'] for r in read_json(ROOT/'outputs/stage14a/v1/stage14a_mathverse788_family_manifest.json')['rows']}
    # Illustrative selection, not a prevalence sample. No protocol is optimized on these cases.
    cases=[
      ('mv_9_image_T_r0','Maze connectivity replaced by a familiar verbal template',
       'The trace expressly appeals to typical maze problems instead of resolving the source path. This is evidence of textual template use in the emitted account, not a measurement of internal image access.',
       "Looking at the maze image",None),
      ('mv_32_image_T_r0','Global containment and imagined standard Venn structure',
       'The original source has four circles and the kangaroo belongs to three. The saved trace repeatedly describes a standard three-circle Venn diagram, oscillates between two and three, and answers two. Current source inspection supports a structural mismatch; the causal reason remains unknown.',
       "Since the user provided an image",None),
      ('mv_2997_image_T_r0','Local height is usable, but the larger shape is misrepresented',
       'The white triangle has height 8, but the source shaded region has an increasing top edge and is a trapezoid, not the asserted 3×8 rectangle. Its two vertical heights are 8 and 12, giving area 30. This supports a global configuration/source-use error rather than failure of the local Pythagorean arithmetic.',
       'Therefore, the shaded region is a rectangle',None),
      ('mv_51_image_T_r0','Endpoint enumeration versus rope identity',
       'Existing source audit identifies six marked free endpoints and no closed rope. The trace lists only five endpoint positions and also treats a dot as the end of a unique rope. This combines source enumeration and an endpoint-to-object reasoning issue; neither a missing endpoint nor a wrong final alone identifies attention location.',
       None,'51_T_c003'),
      ('mv_120_image_T_r0','Local scale/height extraction',
       'The existing source reference places mushroom tops at scale 11 and 6 with common base 0. Thinking explicitly binds the shorter top to 4. This is an audited local value/binding error, showing that not every failure is global.',
       None,'120_T_c003'),
      ('mv_580_image_T_r0','Occluded physical lengths and incorrect comparison proxy',
       'The existing source reference compares equal head heights/common bottom and the projecting tip at screw 1 versus no tip at screw 5. The trace instead claims a U-shaped block and compares threads/visible lengths. This is a source/context comparison failure; final numerical difficulty is not its main observable issue.',
       None,'580_T_c002'),
      ('mv_2831_image_T_r0','Incorrect component arrangement in a global diagram',
       'The existing audit identifies an alternate assumed construction: a central 120-degree arrangement replaces the depicted skinny-triangle arrangement. The source reference says an outer edge is the longest edge of one copy. This is global structural interpretation with mathematical assumptions, not merely tiny-label OCR.',
       'around a common vertex',None),
      ('mv_1118_image_T_r0','Downstream construction after correct minimal source facts',
       'The existing audit says tile sectors are explicitly correct, but later row/column adjacency and border arithmetic/construction are inconsistent. This is supported downstream-use evidence from the prior audit. It is not a proof that every additional visual fact was correct.',
       None,None),
      ('mv_2045_image_T_r0','Source restatement without a successful geometric derivation',
       'The existing audit records eventual source-correct geometry followed by invalid formula/absolute-value repair. A corrected or restated visual premise does not guarantee the solver incorporates it correctly.',
       None,None),
      ('mv_2239_image_T_r0','Correct minimal steps but wrong full-grid coordinate frame',
       'The existing audit says the required 1→2 right and 2→3 down steps are correct, but the partial spiral row is misbound to row 2 of the full 15×15 grid. This illustrates why all minimal E* facts correct does not imply a purely nonvisual downstream failure.',
       None,None),
      ('mv_2925_image_T_r0','Scored failure with a source/gold inconsistency candidate',
       'Thinking derives medial-triangle area 45 from a right triangle with adjacent sides 15 and 24. The archived gold is literal 45^2, so the unchanged official status is WRONG. The stated task supports 45; flag this for human gold review, without correcting the dataset or treating it as an established model failure.',
       'The answer should be 45',None),
      ('verse_7_Vision_Only_native_T_r0','Vision-only ray/angle identity, with contradictory source-QC metadata',
       'Five other native versions are correct and Vision Only is wrong. Its trace claims not to see the figure and guesses the configuration. Detailed source notes explicitly say Text Only is insufficient, although the sufficiency checkbox is PASS. This is an informative interface/geometry case, not a clean six-way causal experiment.',
       "I can't see it",None),
      ('verse_59_Vision_Intensive_native_T_r0','Intermediate modality drops source constraints',
       'Text Dominant, Text Lite, Text Only, Vision Dominant and Vision Only are correct. The failing Vision Intensive version omits parallelism and angle bisection without replacement marks in the shared image. Do not force this documented under-specification case into a pure visual-acquisition failure.',
       "I can't see the figure",None),
      ('verse_90_Vision_Dominant_native_T_r0','Wrong benchmark key rather than convincing model error',
       'All six scored versions are WRONG with native answer B=25 degrees. The source shows a 50-degree central angle and an inscribed angle on the same minor arc, supporting 25 degrees. The existing source review explicitly records the gold C=100-degree conflict. Preserve the scores, but do not interpret the family as a hard reasoning or acquisition failure.',
       "we can't see the figure",None),
    ]
    lines=['# Thinking failure casebook — original sources and exact excerpts','',
      'These are **illustrations selected after the census screen**, not a random prevalence sample. They include counterexamples and source problems as well as explicit visual errors. The full case inventory covers every main wrong/unscorable call. Existing scores and source judgments are unchanged. Narrative explanations distinguish source-observed mismatches from unproven internal causes.','']
    provenance=[]
    for tid,title,note,needle,claimid in cases:
        r=rows[tid];sc=screens[tid];path=ROOT/sc['generation_path'];content=path.read_bytes()
        assert sha(path)==r['generation_sha256']
        raw=json.loads(content)['raw_decoded_response'];m=r['source_metadata'];item=r['item_id']
        quote=None;kind=None
        if claimid:
            claim=next(c for c in audited[item]['traces']['T']['passA']['claims'] if c['claim_id']==claimid)
            quote=claim['quote'];start=claim['span_start'];end=claim['span_end'];kind='historical_exact_claim'
            assert raw[start:end]==quote
        elif needle:
            start=raw.lower().find(needle.lower());assert start>=0,(tid,needle)
            start=max(0,start-100);end=min(len(raw),start+850);quote=raw[start:end];kind='navigation_excerpt'
        else:
            start=raw.rfind('</think>')+len('</think>')
            if start<len('</think>'):start=0
            end=min(len(raw),start+850);quote=raw[start:end];kind='final_response_excerpt'
        lines += [f'## {tid} — {title}','',f"**Archived status:** {r['status']}; **saved answer:** `{r['answer']}`; **gold:** `{m['gold_answer']}`; **tokens:** {r['tokens']:,}.",'',
                  '**Original question / prompt:**','',m['prompt'],'',f"![Original source image]({m['image']})",'',note,'']
        if r['version']:
            lines += ['**Existing source-review note:**','',family_notes[item],'']
        elif item in audited:
            lines += ['**Existing minimal source reference E* (offline audit only):**','',*['- '+x for x in audited[item]['E_star']],'']
        lines += [f'**Exact saved excerpt:** Unicode characters [{start}, {end}); `{kind}`. The excerpt is not the full trace.','', '````text',quote,'````','',
                  f"[Complete original generation]({path}) · [Exact original input]({ROOT/sc['input_path']})",'']
        page=OUT/'case_traces'/f'{tid}.md';page.parent.mkdir(exist_ok=True)
        page.write_text(f'# {tid}: complete raw Thinking response\n\nOriginal status `{r["status"]}`; saved answer `{r["answer"]}`; gold `{m["gold_answer"]}`.\n\n````text\n'+raw+'\n````\n')
        lines += [f'[Read the complete trace, including everything before and after `</think>`]({page})','']
        provenance.append(dict(task_id=tid,generation_path=sc['generation_path'],generation_sha256=r['generation_sha256'],image_path=m['image'],
            image_sha256=m['image_sha256'],excerpt_start=start,excerpt_end=end,quote=quote,kind=kind,
            annotation_source='outputs/stage14d0/viewer/data.js' if item in audited and not r['version'] else None,
            assessment=note))
    target=ROOT/'reports/thinking_math_failure_audit/casebook_20261122.md';target.write_text('\n'.join(lines)+'\n')
    (OUT/'casebook.md').write_text('\n'.join(lines)+'\n')
    save_json(OUT/'casebook_provenance.json',provenance)
    print('Verified exact casebook excerpts and full raw exports:',len(cases))


if __name__=='__main__':main()
