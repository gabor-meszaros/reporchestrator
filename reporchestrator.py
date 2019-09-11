#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate git repository with changes according to a model."""

import calendar
import dataclasses
import itertools
import json
import os
import pickle
import random
import shutil
import sys
import textwrap
import time

try:
    from git import Actor, Repo
except ImportError as err:
    raise ImportError(
        "dependency gitpython not found - "
        "please pip install gitpython. Details %s" % (err,)
    )

try:
    from faker import Faker
except ImportError as err:
    raise ImportError(
        "dependency faker not found - " "please pip install faker. Details %s" % (err,)
    )

# Below due to gitpython 3+ merge of dict 3.5+ dataclasses 3.7+
if tuple(sys.version_info) < (3, 7):
    raise RuntimeError("python version 3.7 or higher required (data classes)")

SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600
DEVELOPER_STRATEGIES = ("random-uniform", "round-robin")


def pairs_to_actors(pairs):
    """Transform a list of pairs to a list of actors."""
    return [Actor(*pair) for pair in pairs]


def activate_model(cfg):
    """Activate the dynamic parts."""
    cfg["fake"] = cfg["fake"]()
    return cfg


def seed_model(cfg):
    """Seed the randomness."""
    cfg["fake"].seed(cfg["random_seed"])
    random.seed(cfg["random_seed"])
    cfg["random_state"] = random.getstate()
    return cfg


def json_from_file(name):
    """System call in one place ..."""
    with open(name) as f_p:
        return json.load(f_p)


def mixin(argv=None):
    """External configuration mixin load."""
    mixin_cfg = {}
    if not argv:
        default_config_path = __file__.replace(".py", ".json")
        if os.path.isfile(default_config_path):
            mixin_cfg = json_from_file(default_config_path)
    elif len(argv) == 1:
        cfg_path_or_text = argv[0]
        if os.path.isfile(cfg_path_or_text):
            mixin_cfg = json_from_file(cfg_path_or_text)
        elif cfg_path_or_text:
            mixin_cfg = json.loads(cfg_path_or_text)

    if mixin_cfg and mixin_cfg.get("developer_data"):
        mixin_cfg["developers"] = pairs_to_actors(mixin_cfg["developer_data"])

    return mixin_cfg


def defaults(argv=None):
    """Layered fill-in of default parameters - any errors not caught."""
    default_cfg = {
        "random_seed": 42,
        "repo_age_in_days": 10,
        "fake": Faker,
        "team_size": 3,
        "developer_strategy": "random-uniform",
        "general_commit_words": ["Add", "an", "empty", "change"],
        "merge_commit_words": ["Introduce", "the", "feature"],
        "max_commits_per_branch": 10,
        "repo_dir": "repository",
        "datetime_format_template": r"%Y-%m-%dT%H:%M:%S",
        "ticket_id_template": r"ACME-%d",
        "message_template": r"%s %s",
    }
    mixin_cfg = mixin(argv)
    cfg = {**default_cfg, **mixin_cfg}

    cfg = activate_model(cfg)
    cfg = seed_model(cfg)

    cfg["developer_data"] = [
        (cfg["fake"].name(), cfg["fake"].email()) for _ in range(cfg["team_size"])
    ]
    cfg["developers"] = pairs_to_actors(cfg["developer_data"])

    if cfg["developer_strategy"] not in DEVELOPER_STRATEGIES:
        raise ValueError(
            "warning: developer selection strategy expected in {} but found ('{}') instead".format(
                DEVELOPER_STRATEGIES, cfg["developer_strategy"]
            )
        )

    return cfg


def next_member(cfg):
    """Return choice from population via strategy."""
    population = cfg["developers"]
    if cfg["developer_strategy"] == "round-robin":
        for member in itertools.cycle(population):
            yield member
    else:
        while True:
            yield random.choice(population)


def choose_in(low, high):
    """Return a random integer in the closed interval."""
    return random.randint(low, high)


def periodic_commit(start, length, split):
    """Return the hourly commit within interval according to split()."""
    return start + split() * length


def blurb(cfg):
    """Commit messages may have longer text explaining the change."""
    if random.choice((True, True, False)):  # 2/3 have such blurb ...
        long_blurb = cfg["fake"].paragraph(
            nb_sentences=random.randint(2, 13),
            variable_nb_sentences=True,
            ext_word_list=None,
        )
        return "\n".join(textwrap.wrap(long_blurb))
    return ""


def text(cfg, phase, high=6):
    """Randomize the content part of a message per phase."""
    short = cfg["fake"].sentence(
        nb_words=high, variable_nb_words=True, ext_word_list=None
    )
    return "{} {}\n\n{}".format(" ".join(cfg[phase]), short, blurb(cfg))


def message_of(cfg, ticket, phase):
    """Generate message according to ticket and phase."""
    return cfg["message_template"] % (ticket, text(cfg, phase))


def create_repository(cfg):
    """Create empty repository as per config."""
    if os.path.isdir(cfg["repo_dir"]):
        shutil.rmtree(cfg["repo_dir"], ignore_errors=True)
    return Repo.init(cfg["repo_dir"])


def commit_datetime_string_gen(cfg):
    """Commit datetime string representation generator from range concept."""
    repo_end_time = calendar.timegm(time.gmtime())
    first_commit_time = repo_end_time - (cfg["repo_age_in_days"] * SECONDS_PER_DAY)
    for raw_date in range(first_commit_time, repo_end_time, SECONDS_PER_HOUR):
        commit_time = periodic_commit(raw_date, SECONDS_PER_HOUR, random.random)
        yield time.strftime(cfg["datetime_format_template"], time.gmtime(commit_time))


def join(cfg, model):
    """Intermediate joining (and freezing) strategy to enable pickling."""
    cfg["fake"] = "Faker"
    cfg["random_state"] = cfg["random_state"][0]
    del cfg["developers"]
    cfg["model"] = str(model)
    return cfg


def author_committer_facts(model, date):
    """Author/Committer facts in git interface."""
    return dict(
        author=model.developer,
        author_date=date,
        committer=model.developer,
        commit_date=date,
    )


def model_plan_feature(cfg, model, developer_gen):
    """Adapt the model for feature development start."""
    model.ticket = cfg["ticket_id_template"] % (choose_in(1, cfg["repo_age_in_days"]),)
    model.planned = choose_in(1, cfg["max_commits_per_branch"])
    model.developer = next(developer_gen)
    return model


def start_feature(repo, cfg, model, developer_gen):
    """Plan feature in model and start development on branch."""
    model = model_plan_feature(cfg, model, developer_gen)
    repo.head.reference = repo.create_head(model.ticket)
    repo.head.reset(index=True, working_tree=True)
    return repo, model


def model_note_change(model, developer_gen, date):
    """Note the upcoming change in model."""
    model.developer = next(developer_gen)
    kwargs = author_committer_facts(model, date)
    model.commits += 1
    return model, kwargs


def add_commit(repo, cfg, model, developer_gen, date):
    """Note the commit in model and update repo."""
    model, kwargs = model_note_change(model, developer_gen, date)
    msg = message_of(
        cfg, model.ticket if model.ticket is not None else "", "general_commit_words"
    )
    repo.index.commit(msg, **kwargs)
    return repo, model


def groom_model(model):
    """Reset the feature indicators."""
    model.commits, model.ticket = 0, None
    return model


def merge_feature(repo, cfg, model, date):
    """Merge the feature in repo and groom the model."""
    repo.index.merge_tree(
        repo.heads.master, base=repo.merge_base(repo.heads.master, repo.head)
    )
    kwargs = {
        **author_committer_facts(model, date),
        **dict(head=True, parent_commits=(repo.heads.master.commit, repo.head.commit)),
    }
    repo.index.commit(message_of(cfg, model.ticket, "merge_commit_words"), **kwargs)
    repo.heads.master.commit = repo.head.commit
    repo.head.reference = repo.heads.master
    repo.delete_head(model.ticket)
    model = groom_model(model)

    return repo, model


@dataclasses.dataclass
class Model:
    """Class for keeping track of consistent model state."""

    developer: Actor = None
    ticket: str = None
    commits: int = 0
    planned: int = 0

    def is_consistent(self) -> bool:
        """Minimal consistency: Never more commits than planned."""
        return self.commits <= self.planned

    def __repr__(self):
        return "Model<developer={}, ticket={}, commits={}, planned={}>".format(
            None
            if not isinstance(self.developer, Actor)
            else str((self.developer.name, self.developer.email)),
            str(self.ticket),
            self.commits,
            self.planned,
        )


def main(argv):
    """Drive the repository orchestration."""
    cfg = defaults(argv)
    repo = create_repository(cfg)
    model = Model()
    developer_gen = next_member(cfg)
    for git_date in commit_datetime_string_gen(cfg):
        repo, model = add_commit(repo, cfg, model, developer_gen, git_date)
        if model.ticket is not None and model.commits == model.planned:
            repo, model = merge_feature(repo, cfg, model, git_date)
        if model.ticket is None:
            repo, model = start_feature(repo, cfg, model, developer_gen)
    cfg = join(cfg, model)
    with open("model.pickle", "wb") as f_p:
        pickle.dump(cfg, f_p, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # skip the script name
