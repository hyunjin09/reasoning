from visual_reasoning.stage3b9.evidence import build_candidate_text, find_evidence_mentions


def test_candidate_text_normalizes_spacing():
    assert build_candidate_text("sphere radius", "3", " cm") == " the sphere radius is 3 cm"
    assert build_candidate_text("cone height", "12.5", "") == " the cone height is 12.5"


def test_mentions_include_full_target_keywords_and_value():
    text = "Okay. The cone has height 12.5 cm and radius 4.1 cm."
    mentions = find_evidence_mentions(text, target="cone height", original_value="12.5")
    assert [row["term"] for row in mentions] == ["cone", "height", "12.5"]
    assert [row["character_start"] for row in mentions] == sorted(row["character_start"] for row in mentions)


def test_integer_mention_allows_sentence_period_but_not_decimal_prefix():
    text = "The height is 6. The other measure is 6.5."
    mentions = find_evidence_mentions(text, target="cone height", original_value="6")
    values = [row for row in mentions if row["term"] == "6"]
    assert [row["matched_text"] for row in values] == ["6"]
