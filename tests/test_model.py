from unittest import mock

import pytest

from context import reporchestrator


def test_choose_in():
    low, high = 1, 3
    chosen = reporchestrator.choose_in(low, high)
    assert low <= chosen <= high


def test_periodic_commit():
    def split():
        return 42
    commit = reporchestrator.periodic_commit(1, 2, split)
    assert commit == 85


def test_next_member():
    c = {"developers": ["a", "b"], "developer_strategy": "round-robin"}
    gen = reporchestrator.next_member(c)
    m = next(gen)
    assert m == "a"
    m = next(gen)
    assert m == "b"
    m = next(gen)
    assert m == "a"


def test_next_member_random_uniform():
    c = {"developers": ["a", "b"], "developer_strategy": "random-uniform"}
    gen = reporchestrator.next_member(c)
    m = next(gen)
    assert m in ("a", "b")


def test_commit_datetime_string_gen():
    c = {"repo_age_in_days": 1, "datetime_format_template": r"%Y"}
    gen = reporchestrator.commit_datetime_string_gen(c)
    u, v = next(gen), next(gen)
    assert u == v
    assert len(u) == 4
    assert u.startswith("2")


def test_model_class():
    m = reporchestrator.Model()
    m_rep = "Model<developer=None, ticket=None, commits=0, planned=0>"
    assert str(m) == m_rep
    assert m.is_consistent()


def test_join():
    c = {"fake": "change_this", "random_state": [42, -1], "developers": True}
    c = reporchestrator.join(c, reporchestrator.Model())
    assert c["fake"] != "random_state"
    assert c["random_state"] == 42
    assert not c.get("developers")


def test_blurb():
    from faker import Faker
    fake = Faker()
    fake.seed(42)
    c = {"fake": fake}
    has_text = False
    for _ in range(9):
        t = reporchestrator.blurb(c)
        if t:
            has_text = True
            assert "." in t
    assert has_text  # HACK A DID ACK


def test_text():
    from faker import Faker
    fake = Faker()
    fake.seed(42)
    p = "a_phase"
    p_data = ["foo", "bar", "baz"]
    c = {"fake": fake, p: p_data}
    nb_words = 3
    t = reporchestrator.text(c, p, nb_words)
    assert "\n" in t
    assert " ".join(p_data) in t


def test_message_of():
    from faker import Faker
    fake = Faker()
    fake.seed(42)
    p = "a_phase"
    p_data = ["foo", "bar", "baz"]
    c = {"fake": fake, p: p_data, "message_template": r"%s %s"}
    tid = "ACME-123"
    t = reporchestrator.message_of(c, tid, p)
    assert "\n" in t
    assert t.startswith(tid)
    assert " ".join(p_data) in t


def test_author_committer_facts():
    m = reporchestrator.Model()
    t = "42"
    d_expected = dict(
        author=m.developer,
        author_date=t,
        committer=m.developer,
        commit_date=t
    )
    d = reporchestrator.author_committer_facts(m, "42")
    assert d == d_expected


def test_model_plan_feature():
    import git
    m = reporchestrator.Model()
    c = {
        "developers": [git.Actor("a", "b"), git.Actor("c", "d")],
        "repo_age_in_days": 1,
        "developer_strategy": "round-robin",
        "max_commits_per_branch": 3,
        "ticket_id_template": r"ACME-%d",
    }
    gen = reporchestrator.next_member(c)
    m = reporchestrator.model_plan_feature(c, m, gen)
    assert m.developer == git.Actor("a", "b")
    assert m.is_consistent()
    assert m.ticket == "ACME-1"
    assert 1 <= m.planned <= c["max_commits_per_branch"]
    m = reporchestrator.model_plan_feature(c, m, gen)
    assert m.developer == git.Actor("c", "d")


def test_model_note_change():
    import git
    m = reporchestrator.Model()
    t = "42"
    c = {
        "developers": [git.Actor("e", "f"), git.Actor("c", "d")],
        "developer_strategy": "round-robin",
    }
    gen = reporchestrator.next_member(c)
    m, k = reporchestrator.model_note_change(m, gen, t)
    k_expected = dict(
        author=m.developer,
        author_date=t,
        committer=m.developer,
        commit_date=t,
    )
    assert m.developer == git.Actor("e", "f")
    assert not m.is_consistent()
    assert m.ticket is None
    assert m.planned == 0
    assert m.commits == 1
    assert k == k_expected
    m, k = reporchestrator.model_note_change(m, gen, t)
    assert m.developer == git.Actor("c", "d")


def test_groom_model():
    m = reporchestrator.Model()
    m.ticket = "ACME-42"
    m.commits = 42
    assert not m.is_consistent()
    m = reporchestrator.groom_model(m)
    assert m.is_consistent()
    assert m.commits == 0
    assert m.ticket is None  # Important as this triggers feature planning


@mock.patch('shutil.rmtree')
@mock.patch('git.Repo.init')
def test_repo_init(ri_mock, rm_mock):  # left corresponds to outer
    a_dir = "foo"
    rm_mock.return_value = 'REMOVED'
    ri_mock.return_value = 'SUCCESS'

    reporchestrator.create_repository({"repo_dir": a_dir})

    rm_mock.assert_called_with(a_dir, ignore_errors=True)
    assert rm_mock.return_value == 'REMOVED'
    ri_mock.assert_called_with(a_dir)
    assert ri_mock.return_value == 'SUCCESS'
