set -ex

export GIRA_TEST_ROOT=$PWD

#### Prepare the test #######################
## Untar git remote for the tests
pushd remote
rm -rf dep1
tar -xf dep1.tar
popd

rm -rf local
mkdir -p local/poetry local/dynamic
envsubst < local-template/poetry/pyproject.toml > local/poetry/pyproject.toml
envsubst < local-template/poetry/poetry.lock > local/poetry/poetry.lock
envsubst < local-template/pyproject.toml > local/pyproject.toml
envsubst < local-template/pubspec.yaml > local/pubspec.yaml
envsubst < local-template/west.yml > local/west.yml
envsubst < local-template/west.yml > local/west-SOMETHING.yaml
envsubst < local-template/.gira.yaml > local/.gira.yaml
envsubst < local-template/prefix.yaml > local/prefix.yaml
envsubst < local-template/dynamic/pyproject.toml > local/dynamic/pyproject.toml
envsubst < local-template/dynamic/requirements.txt > local/dynamic/requirements.txt


function not_contains {
    grep -q $1 $2 || return 0
}

pushd local
git init 2> /dev/null
git config user.name "Test Action" && git config user.email ""
git add .
git commit -m "Initial commit"
INITIAL_COMMIT=$(git rev-parse HEAD)

# run on no changes in dependencies
echo "-- Test no changes" > README.md
gira
git reset README.md
rm README.md

#############################################
## run tests
echo "-- Test poetry/pyproject.toml"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.1/g' poetry/pyproject.toml
gira -c  poetry/pyproject.toml -v > output.txt
grep dep1-poetry output.txt
grep "1.0.0" output.txt
grep "1.1.1" output.txt
grep OCD-1234 output.txt
grep OCD-567 output.txt


echo "-- Test pyproject.toml"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.0/g' pyproject.toml
gira -c pyproject.toml > output.txt
grep dep1-pytoml output.txt
grep "1.0.0" output.txt
grep "1.1.0" output.txt
grep OCD-1234 output.txt
not_contains OCD-567 output.txt


echo "-- Test project.optional-dependencies"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
# bump only the dep living in the [project.optional-dependencies] dev group
sed -i 's/dep1-opt==1.0.0/dep1-opt==1.1.0/' pyproject.toml
gira -c pyproject.toml > output.txt
grep dep1-opt output.txt
grep "1.0.0" output.txt
grep "1.1.0" output.txt
grep OCD-1234 output.txt
not_contains OCD-567 output.txt


echo "-- Test range-pinned dependency (lower bound)"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
# bump only the lower bound of the range-pinned dep: >=1.0.0 -> >=1.1.0
sed -i 's/dep1-range >=1.0.0/dep1-range >=1.1.0/' pyproject.toml
gira -c pyproject.toml > output.txt
grep dep1-range output.txt
grep "1.0.0" output.txt
grep "1.1.0" output.txt
grep OCD-1234 output.txt
not_contains OCD-567 output.txt

# unit-level coverage of the specifier handling (==, >=, ~=, extras, unpinned)
python3 - <<'PY'
from gira.deps import parse_pytoml
obs = {"a", "b", "c", "d", "e"}
content = '''
[project]
name = "x"
dependencies = [
  "a >=1.13.0, <2.0",
  "b ==0.14.0",
  "c[extra] ~=2.3.4 ; python_version < '3.11'",
  "d > 2.1",
  "e",
]
'''
got = parse_pytoml(content, obs)
assert got == {"a": "v1.13.0", "b": "v0.14.0", "c": "v2.3.4", "d": "v2.1"}, got
print("specifier unit checks passed")
PY


echo "-- Test setuptools dynamic dependencies (requirements.txt)"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
# bump the pinned dep in requirements.txt - pyproject.toml itself is unchanged
sed -i 's/1.0.0/1.1.1/g' dynamic/requirements.txt
gira -c dynamic/pyproject.toml > output.txt
grep dep1-req output.txt
grep "1.0.0" output.txt
grep "1.1.1" output.txt
grep OCD-1234 output.txt
grep OCD-567 output.txt


echo "-- Test pubspec.yaml"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.1/g' pubspec.yaml
gira -c pubspec.yaml > output.txt
grep dep1-pubspec output.txt
grep OCD-1234 output.txt
grep OCD-567 output.txt


echo "-- Test pubspec.yaml"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.0/g' west.yml
gira -c west.yml > output.txt
grep dep1-west output.txt
grep OCD-1234 output.txt
not_contains OCD-567 output.txt


echo "-- Test west-SOMETHING.yaml"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.0/g' west-SOMETHING.yaml
gira -c west-SOMETHING.yaml > output.txt
grep dep1-west output.txt
grep OCD-1234 output.txt
not_contains OCD-567 output.txt


echo "-- Test JIRA key prefix filtering"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.0/g' west.yml
# auto-detection (no configured prefix) finds the OCD-* ticket
gira -c west.yml > output.txt
grep dep1-west output.txt
grep OCD-1234 output.txt
# with jira.prefix=DH the OCD-* ticket is filtered out (change still reported via -a)
rm -rf .gira_cache output.txt
gira -c prefix.yaml -a > output.txt
grep dep1-west output.txt
not_contains OCD-1234 output.txt

# prefix matching at the unit level: default auto-detect, single and multiple prefixes
python3 - <<'PY'
from gira import jira
assert jira.extract_ticket_names("fix ABC-1 and DH-22") == ["ABC-1", "DH-22"]
assert jira.extract_ticket_names("ABC-1 DH-22 OCD-3", jira.ticket_pattern("DH")) == ["DH-22"]
assert jira.extract_ticket_names("ABC-1 DH-22 OCD-3", jira.ticket_pattern(["DH", "OCD"])) == [
    "DH-22",
    "OCD-3",
]
print("prefix unit checks passed")
PY


echo "-- Test moving from 1.0.0 to 1.1.0 and then to 1.1.1"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.0/g' west.yml
gira -c west.yml > output.txt
grep OCD-1234 output.txt
not_contains OCD-567 output.txt
# now move to 1.1.1
sed -i 's/1.1.0/1.1.1/g' west.yml
gira -c west.yml > output.txt
grep OCD-1234 output.txt
grep OCD-567 output.txt

# Use the state of previous test that ended in 1.1.1 version
# Cuz we need 1.1.1 -> 1.1.2 to check dependency mention without JIRA tickets
echo "-- test the --all switch"
git add west.yml
git commit -m "fix: bump 1.1.1"
sed -i 's/1.1.1/1.1.2/g' west.yml
gira -c west.yml --all > output.txt
cat output.txt
not_contains OCD-1234 output.txt
not_contains OCD-567 output.txt
grep "1.1.1" output.txt
grep "1.1.2" output.txt


echo "-- Test renames in .bb files"
git reset --hard $INITIAL_COMMIT
echo "checksum=abc\nurl=ahoj.com\n" > dep1_1.0.0.bb
git add dep1_1.0.0.bb
git commit -m "feat: Add dep1 bb"

# now move to 1.1.0
git mv dep1_1.0.0.bb dep1_1.1.0.bb
echo "checksum=abd\nurl=ahoj.com\n" > dep1_1.1.0.bb
gira > output.txt
grep OCD-1234 output.txt  # classic check for move to version 1.1.0 but not to 1.1.1
not_contains OCD-567 output.txt


echo "-- Test pre-commit"
git reset --hard $INITIAL_COMMIT
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.1/g' west.yml
echo "" > .git/COMMIT_EDITMSG  # clear the commit message
gira -c west.yml .git/COMMIT_EDITMSG
grep OCD-1234 .git/COMMIT_EDITMSG  # gira should output there instead of stdout
grep OCD-567 .git/COMMIT_EDITMSG  # gira should output there instead of stdout

echo "should stay" > randomFile.txt
gira -c west.yml randomFile.txt  # gira must not override anything else than the commit message file
grep "should stay" randomFile.txt  # gira should not touch the file
not_contains OCD-1234 randomFile.txt
not_contains OCD-567 randomFile.txt


popd

#############################################
## cleanup local
rm -rf local

## cleanup remote
pushd remote
rm -rf dep1
popd
