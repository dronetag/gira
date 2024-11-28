# Tests

Here are tests that deal with git repositories. The "remote" is TARed in remote/
folder and extracted at the begging of the test. Since file:// remotes must be
specified with absolute path then we have the local-template repository where
$GIRA_TEST_ROOT is being replaced (with pretty much just value of $PWD).


## Modify remote

We kept conveniently whole dep1 repository so you can just unTAR it, make commits
and then TAR it again. All of this just to avoid having sub-repositories in gira
repository.


## Test workings

Tests do `git init` and then make commits/changes so the .git repository does not
need to be part of gira repository.

For your convenience - there is a `git log` of tha TARed repository dep1

```git
commit 8abae70f337d764e3ffa2ef0637c9eda24d25250 (HEAD -> main, tag: v1.1.1)
Author: Tomas Peterka <tomas@peterka.me>
Date:   Mon Feb 5 17:03:53 2024 +0100

    fix: add new line at the end of file OCD-567

commit 42c27a3e66153a4a5f6317e8adbc4a8d17dad99c (tag: v1.1.0)
Author: Tomas Peterka <tomas@peterka.me>
Date:   Mon Feb 5 15:50:59 2024 +0100

    feat: add word for better explanation OCD-1234 #close

commit db11bb42fa82b1f39fdf9ad2fd8a579c7e8f5421
Author: Tomas Peterka <tomas@peterka.me>
Date:   Mon Feb 5 15:40:38 2024 +0100

    fix: grammar OCD-1234

commit ac804edac73e0494cbfabc8fc1b33c5b1aeafffe (tag: v1.0.0)
Author: Tomas Peterka <tomas@peterka.me>
Date:   Mon Feb 5 15:38:44 2024 +0100

    initial commit
```
