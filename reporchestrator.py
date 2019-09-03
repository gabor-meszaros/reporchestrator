from calendar import timegm
from git import Actor, Repo
from random import randint
from shutil import rmtree
from time import gmtime, strftime

REPO_AGE_IN_DAYS = 10

SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600
HOURS_PER_DAY = 24
LAST_HOUR_INDEX = HOURS_PER_DAY - 1

ACTOR_NAME = "John Doe"
ACTOR_EMAIL = "john-doe@users.noreply.github.com"

GENERAL_COMMIT_MESSAGE = "Add an empty change"
MERGE_COMMIT_MESSAGE = "Introduce the feature"

REPO_DIR = "repository"

rmtree(REPO_DIR, ignore_errors=True)
repo = Repo.init(REPO_DIR)
first_commit_time = timegm(gmtime()) - (REPO_AGE_IN_DAYS * SECONDS_PER_DAY)
branch_ticket = None

for day_offset in range(0, REPO_AGE_IN_DAYS):
    for hour_offset in range(0, HOURS_PER_DAY):
        unformatted_date = first_commit_time + (day_offset * SECONDS_PER_DAY) \
                           + (hour_offset * SECONDS_PER_HOUR)
        date = strftime("%Y-%m-%dT%H:%M:%S", gmtime(unformatted_date))
        index = repo.index
        author = Actor(ACTOR_NAME, ACTOR_EMAIL)
        committer = Actor(ACTOR_NAME, ACTOR_EMAIL)
        ticket_reference = branch_ticket if branch_ticket is not None else ""
        message = "{} {}".format(ticket_reference, GENERAL_COMMIT_MESSAGE)
        index.commit(message, author=author, committer=committer,
                     author_date=date, commit_date=date)
        if (branch_ticket is not None) and (hour_offset == LAST_HOUR_INDEX):
            master = repo.heads.master
            branch = repo.head
            merge_base = repo.merge_base(master, branch)
            repo.index.merge_tree(master, base=merge_base)
            message = "{} {}".format(branch_ticket, MERGE_COMMIT_MESSAGE)
            repo.index.commit(message, parent_commits=(master.commit,
                                                       branch.commit),
                              head=True, author=author, committer=committer,
                              author_date=date, commit_date=date)
            master.commit = repo.head.commit
            repo.head.reference = master
            repo.delete_head(branch_ticket)
            branch_ticket = None
        if (branch_ticket is None) and (day_offset != REPO_AGE_IN_DAYS - 1):
            branch_ticket = "ACME-" + str(randint(1, REPO_AGE_IN_DAYS))
            branch = repo.create_head(branch_ticket)
            repo.head.reference = branch
            repo.head.reset(index=True, working_tree=True)