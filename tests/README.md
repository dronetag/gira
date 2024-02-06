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
