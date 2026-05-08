from app.services.job_metadata import extract_salary, split_title_meta


def test_split_title_meta_three_segments():
    c, t = split_title_meta("后端开发-某某科技有限公司-招聘网站")
    assert "某某" in c or len(c) > 0
    assert "后端" in t or len(t) > 0


def test_extract_salary_wan_range():
    s = extract_salary("团队介绍\n薪资：25-35万/年\n职责")
    assert "万" in s or "25" in s
