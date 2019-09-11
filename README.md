# Reporchestrator

A tool that helps you to orchestrate Git repositories mainly for training purposes.

## Usage

You can generate a repository by running the script without parameters:

```
./reporchestrator.py
```

The result will be placed to the "repository" directory.

## Configuration

The script expects one of three external configuration sources
that are mixed in the following order (first overrides last):

1. command line json string as argument
2. command line json file name as argument
3. default values in json file `reporchestrator.json`
4. default values in source code

The current default parameters in `reporchestrator.json` are:

```
{
    "random_seed": 22,
    "repo_age_in_days": 10,
    "team_size": 5,
    "general_commit_words": ["Add", "an", "empty", "change"],
    "merge_commit_words": ["Introduce", "the", "feature"],
    "max_commits_per_branch": 10,
    "repo_dir": "repository",
    "datetime_format_template": "%Y-%m-%dT%H:%M:%S",
    "ticket_id_template": "ACME-%d",
    "message_template": "%s %s"
}
```

For detailed hierarchical configuration resolution see the 
source code for now.

## Model documentation

When run, the tool writes a model.pickle file which can be
viewed like so (example data from a random run):
```
 python -m pickle model.pickle 
{'datetime_format_template': '%Y-%m-%dT%H:%M:%S',
 'developer_data': [('Brenda Johnson', 'martinezdenise@yahoo.com'),
                    ('Crystal Chung', 'sarah60@smith-baker.com'),
                    ('Brian Schmidt', 'dclements@gmail.com'),
                    ('Cody Long', 'ablanchard@gmail.com'),
                    ('Michael Reynolds', 'nbarnes@khan.org')],
 'developer_strategy': 'random-uniform',
 'fake': 'Faker',
 'general_commit_words': ['Add', 'an', 'empty', 'change'],
 'max_commits_per_branch': 10,
 'merge_commit_words': ['Introduce', 'the', 'feature'],
 'message_template': '%s %s',
 'model': "Model<developer=('Brenda Johnson', 'martinezdenise@yahoo.com'), "
          'ticket=ACME-3, commits=7, planned=8>',
 'random_seed': 22,
 'random_state': 3,
 'repo_age_in_days': 10,
 'repo_dir': 'repository',
 'team_size': 5,
 'ticket_id_template': 'ACME-%d'}
```

## Dependencies

This tool depends on the non-standard library python modules 

1. `gitpython` to interact with git repositories 
2. and `faker` to easily create surrogate data like user names and email addresses 

## Contributing

First of all: 
>Every contribution abiding by the license is highly appreciated!

Before starting developing:

1. Please install the dev and test requirements before development.
2. Please also check the existing issues and refer to an issue.
3. If you want to provide an improvement or fix a bug not recorded as issue, consider submitting an issue.

Before submitting a pull please ensure the change set 
satisfies all of the following 4 criteria:

1. `black reporchestrator.py` succeeded
2. `pylint reporchestrator.py` ideally 10.0/10.0 score
3. `pytest` has no failing test
4. `pytest --cov-report term --cov=reporchestrator tests/` should report 80% coverage or more (especially if new features were added)

Thank you.

