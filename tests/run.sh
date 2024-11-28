set -ex

export GIRA_TEST_ROOT=$PWD

#### Prepare the test #######################
## Untar git remote for the tests
pushd remote
rm -rf dep1
tar -xf dep1.tar
popd

rm -rf local
mkdir -p local/poetry
envsubst < local-template/poetry/pyproject.toml > local/poetry/pyproject.toml
envsubst < local-template/poetry/poetry.lock > local/poetry/poetry.lock
envsubst < local-template/pyproject.toml > local/pyproject.toml
envsubst < local-template/pubspec.yaml > local/pubspec.yaml
envsubst < local-template/west.yml > local/west.yml
envsubst < local-template/.gira.yaml > local/.gira.yaml


pushd local
git init 2> /dev/null
git config user.name "Test Action" && git config user.email ""
git add .
git commit -m "Initial commit"

# run on no changes in dependencies
echo "-- Test no changes" > README.md
gira
git reset README.md
rm README.md

#############################################
## run tests
echo "-- Test poetry/pyproject.toml"
git reset --hard
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.1/g' poetry/pyproject.toml
gira -c  poetry/pyproject.toml -v > output.txt
grep dep1-poetry output.txt
grep "1.0.0" output.txt
grep "1.1.1" output.txt
grep OCD-1234 output.txt
grep OCD-567 output.txt


echo "-- Test pyproject.toml"
git reset --hard
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.0/g' pyproject.toml
gira -c pyproject.toml > output.txt
grep dep1-pytoml output.txt
grep "1.0.0" output.txt
grep "1.1.0" output.txt
grep OCD-1234 output.txt
grep -v OCD-567 output.txt


echo "-- Test pubspec.yaml"
git reset --hard
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.1/g' pubspec.yaml
gira -c pubspec.yaml > output.txt
grep dep1-pubspec output.txt
grep OCD-1234 output.txt
grep OCD-567 output.txt


echo "-- Test pubspec.yaml"
git reset --hard
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.0/g' west.yml
gira -c west.yml > output.txt
grep dep1-west output.txt
grep OCD-1234 output.txt
grep -v OCD-567 output.txt


echo "-- Test moving from 1.0.0 to 1.1.0 and then to 1.1.1"
git reset --hard
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.0/g' west.yml
gira -c west.yml > output.txt
grep OCD-1234 output.txt
grep -v OCD-567 output.txt
# now move to 1.1.1
sed -i 's/1.1.0/1.1.1/g' west.yml
gira -c west.yml > output.txt
grep OCD-1234 output.txt
grep OCD-567 output.txt


echo "-- Test pre-commit"
git reset --hard
rm -rf .gira_cache output.txt
sed -i 's/1.0.0/1.1.1/g' west.yml
echo "" > .git/COMMIT_EDITMSG  # clear the commit message
gira -c west.yml .git/COMMIT_EDITMSG
grep OCD-1234 .git/COMMIT_EDITMSG  # gira should output there instead of stdout
grep OCD-567 .git/COMMIT_EDITMSG  # gira should output there instead of stdout

echo "should stay" > randomFile.txt
gira -c west.yml randomFile.txt  # gira must not override anything else than the commit message file
grep "should stay" randomFile.txt  # gira should not touch the file
grep -v OCD-1234 randomFile.txt
grep -v OCD-567 randomFile.txt

popd

#############################################
## cleanup local
rm -rf local

## cleanup remote
pushd remote
rm -rf dep1
popd
