from playtest_triage.dedup import merge_similar, similarity


def test_identical_items_merge_ignoring_case_and_punctuation():
    merged = merge_similar(["Too dark in the lab.", "too dark in the lab"])
    assert merged == [("Too dark in the lab.", 2)]


def test_near_duplicates_merge_and_keep_first_phrasing():
    a = "The footstep sound kept looping after I stopped moving in the packaged build."
    b = "Footstep sound kept looping after I stopped moving in the packaged build!"
    merged = merge_similar([a, b])
    assert merged == [(a, 2)]


def test_distinct_items_do_not_merge():
    merged = merge_similar(
        ["The monster is too fast", "I love the sliding mechanic"]
    )
    assert [count for _, count in merged] == [1, 1]


def test_threshold_one_requires_exact_normalized_match():
    merged = merge_similar(["alpha beta", "alpha beta gamma"], threshold=1.0)
    assert len(merged) == 2


def test_similarity_is_symmetric_and_bounded():
    a, b = "game is too dark", "way too dark in the game"
    assert similarity(a, b) == similarity(b, a)
    assert 0.0 <= similarity(a, b) <= 1.0
