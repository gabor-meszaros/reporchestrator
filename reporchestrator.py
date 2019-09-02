from calendar import timegm
from git import Actor, Repo
from shutil import rmtree
from time import gmtime, strftime

REPO_AGE_IN_DAYS = 10

SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600

ACTOR_NAME = "John Doe"
ACTOR_EMAIL = "john-doe@users.noreply.github.com"

GENERAL_COMMIT_MESSAGE = "Add an empty change"

REPO_DIR = "repository"

rmtree(REPO_DIR, ignore_errors=True)
repo = Repo.init(REPO_DIR)
first_commit_time = timegm(gmtime()) - (REPO_AGE_IN_DAYS * SECONDS_PER_DAY)

for day_offset in range(0, REPO_AGE_IN_DAYS):
    for hour_offset in range(0, 24):
        unformatted_date = first_commit_time + (day_offset * SECONDS_PER_DAY) + (hour_offset * SECONDS_PER_HOUR)
        date = strftime("%Y-%m-%dT%H:%M:%S", gmtime(unformatted_date))
        index = repo.index
        author = Actor(ACTOR_NAME, ACTOR_EMAIL)
        committer = Actor(ACTOR_NAME, ACTOR_EMAIL)
        index.commit(GENERAL_COMMIT_MESSAGE, author=author, committer=committer, author_date=date, commit_date=date)
