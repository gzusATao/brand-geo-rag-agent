import pytest

from app.services.extraction_service import extract_brands

PROJECT = {"brand": "星河协作", "aliases": ["星河"], "competitors": ["云帆办公"]}


@pytest.mark.parametrize(
    "answer,recommended,rank",
    [
        ("推荐星河协作。", True, None),
        ("不推荐星河协作。", False, None),
        ("是否推荐星河协作？", False, None),
        ("1. 推荐星河协作。", True, 1),
        ("1. 星河协作提供团队服务。", False, None),
        ("0. 推荐星河协作。", True, None),
        ("如果预算足够，星河协作可以进一步了解。", False, None),
        ("星河协作，推荐云帆办公。", False, None),
    ],
)
def test_conservative_extraction(answer, recommended, rank):
    result = extract_brands(answer, PROJECT)[0]
    assert result["mentioned"] is True
    assert result["recommended"] is recommended
    assert result["rank"] == rank


def test_english_alias_word_boundary():
    project = {"brand": "Arc", "aliases": [], "competitors": []}
    assert extract_brands("Recommend Architecture tools", project)[0]["mentioned"] is False
    assert extract_brands("Arc 是工具", project)[0]["mentioned"] is True
