"""Merge identical pre-gold literal reviews from fixed batches, without re-review."""
from scripts.stage11c.common import ROOT, load, save, sha, now
from scripts.stage11c.answer_review import seal


def main():
    label='native_early'
    full_path=ROOT/'packets'/f'{label}_answer_review.json'
    full={r['packet_id']:r for r in load(full_path)['rows']}
    assert len(full)==32
    selected={};sources={}
    for part in range(4):
        part_label=f'native_early_b{part}'
        packet_path=ROOT/'packets'/f'{part_label}_answer_review.json'
        review_path=ROOT/'annotations'/f'{part_label}_answer_review.json'
        packets=load(packet_path)['rows'];review=load(review_path)
        assert len(packets)==len(review['rows'])==8 and review['sealed']
        assert review['gold_or_correctness_opened'] is False and review['packet_sha256']==sha(packet_path)
        assert {r['packet_id'] for r in packets}=={r['packet_id'] for r in review['rows']}
        for packet in packets:
            assert packet==full[packet['packet_id']], 'No changed text/options/metadata may reuse a review'
        for row in review['rows']:
            ident=row['packet_id'];assert ident not in selected
            selected[ident]=dict(row,source_review_sha256=sha(review_path))
        sources[part_label]=dict(packet_sha256=sha(packet_path),review_sha256=sha(review_path))
    assert set(selected)==set(full)
    for ident,row in selected.items():
        save(ROOT/'audit/answer_drafts'/label/f'{ident}.json',row)
    seal(label)
    save(ROOT/'audit/literal_review_reuse.json',dict(at=now(),full_packet_sha256=sha(full_path),
        sources=sources,identical_rows_checked=32,duplicate_reviews=0,gold_not_joined_before_all_reviews_sealed=True))
    print('SEALED32_IDENTICAL_LITERAL_REVIEWS_NO_GOLD_JOIN')


if __name__=='__main__':
    main()
