## 1.0.7 (https://github.com/dronetag/gira/compare/v1.0.6...v1.0.7) (2024-05-07)

### Bug Fixes

    * commit format - add indentation into line len b74b1ee

## 1.0.6 (https://github.com/dronetag/gira/compare/v1.0.5...v1.0.6) (2024-05-03)

### Bug Fixes

    * allow empty observed conf when submodules on e8c9c05

## 1.0.5 (https://github.com/dronetag/gira/compare/v1.0.4...v1.0.5) (2024-05-02)

### Bug Fixes

    * exclude last commit for ticket extraction 0e43750

## 1.0.4 (https://github.com/dronetag/gira/compare/v1.0.3...v1.0.4) (2024-3-6)

### Bug Fixes

    * better handling JIRA auth error 069a63c
    * make sure that commit format is under 72 chars 6a5dc8d

## 1.0.3 (https://github.com/dronetag/gira/compare/v1.0.2...v1.0.3) (2024-3-6)

### Bug Fixes

    * commit-formatter newline bug d937776

## 1.0.2 (https://github.com/dronetag/gira/compare/v1.0.1...v1.0.2) (2024-2-27)

### Bug Fixes

    * now missing revision in dependency won't crash the app 7e01430

## 1.0.1 (https://github.com/dronetag/gira/compare/v1.0.0...v1.0.1) (2024-2-26)

### Bug Fixes

    * support both YAML extensions: .yml and .yaml 5843727

# 1.0.0 (https://github.com/dronetag/gira/compare/v0.10.0...v1.0.0) (2024-2-16)

### Bug Fixes

    * commit formatter correctly indents new lines 3696c80
    * commit formatter follows more commit msg conventions bdfde78
    * config file types are exclusive 761487b
    * fail if no gira configuration in given config file d86f0f2
    * JIRA config parsing f311fee
    * make Jira url mandatory if token exists 91c4d4a
    * more informative tests run b58b531
    * tests aea93a0
    * feat!: remove support for lock files 34b768a

### Features

    * commit format is git-trailer-like ec25576
    * correctly expand C:\Users\tomas and on windows 5f66294
    * gira survives new (added) dependency files to git 906d168

### BREAKING CHANGES

    * we prefer dependency configuration files over lock files from two reasons:
        1. the config file must always be there in order to generate the lock file
        2. some teams don't commit lock files

# 0.10.0 (2024-2-14)

### Bug Fixes

    * better formatting of tickets with no details
    * do not fail on new repositories
    * postpone JIRA connection
    * rename editorconfig file

### Features

    * do not run in CI/runners
    * JIRA config supports file: and env: prefixes
