from calendar import timegm
from git import Actor, Repo
from random import randint
from shutil import rmtree
from time import gmtime, strftime

REPO_AGE_IN_DAYS = 10

SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600
HOURS_PER_DAY = 24

DEVELOPERS = [ Actor("John Doe", "john-doe@users.noreply.github.com"),
               Actor("Jane Doe", "jane-doe@users.noreply.github.com"),
               Actor("Max Mustermann",
                     "max-mustermann@users.noreply.github.com") ]

GENERAL_COMMIT_MESSAGE = "Add an empty change"
MERGE_COMMIT_MESSAGE = "Introduce the feature"

MAX_COMMITS_PER_BRANCH = 10

REPO_DIR = "repository"

rmtree(REPO_DIR, ignore_errors=True)
repo = Repo.init(REPO_DIR)
repo_end_time = timegm(gmtime())
first_commit_time = repo_end_time - (REPO_AGE_IN_DAYS * SECONDS_PER_DAY)
branch_ticket = None
branch_developer = 0
branch_commits = 0
branch_planned_commits = 0

for raw_date in range(first_commit_time, repo_end_time, SECONDS_PER_HOUR):
    date = strftime("%Y-%m-%dT%H:%M:%S", gmtime(raw_date))
    index = repo.index
    developer = DEVELOPERS[branch_developer]
    ticket_reference = branch_ticket if branch_ticket is not None else ""
    message = "{} {}".format(ticket_reference, GENERAL_COMMIT_MESSAGE)
    index.commit(message, author=developer, committer=developer,
                 author_date=date, commit_date=date)
    branch_commits = branch_commits + 1
    if (branch_ticket is not None) and \
       (branch_commits == branch_planned_commits):
        master = repo.heads.master
        branch = repo.head
        merge_base = repo.merge_base(master, branch)
        repo.index.merge_tree(master, base=merge_base)
        message = "{} {}".format(branch_ticket, MERGE_COMMIT_MESSAGE)
        repo.index.commit(message, parent_commits=(master.commit,
                                                   branch.commit),
                          head=True, author=developer, committer=developer,
                          author_date=date, commit_date=date)
        master.commit = repo.head.commit
        repo.head.reference = master
        repo.delete_head(branch_ticket)
        branch_commits = 0
        branch_ticket = None
    if branch_ticket is None:
        branch_ticket = "ACME-" + str(randint(1, REPO_AGE_IN_DAYS))
        branch_developer = (branch_developer + 1) % len(DEVELOPERS)
        branch = repo.create_head(branch_ticket)
        repo.head.reference = branch
        repo.head.reset(index=True, working_tree=True)
        branch_planned_commits = randint(1, MAX_COMMITS_PER_BRANCH)