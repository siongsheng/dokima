# init — Validation Criteria

## Smoke test (greenfield)

```bash
# Fresh directory
mkdir /tmp/test-init && cd /tmp/test-init

# Run init
hermes-panel init "A simple CLI todo app" .

# Verify outputs
test -f specs/mission.md     || echo "FAIL: no mission.md"
test -f specs/tech-stack.md  || echo "FAIL: no tech-stack.md"
test -f specs/roadmap.md     || echo "FAIL: no roadmap.md"
test -f specs/conventions.md || echo "FAIL: no conventions.md"
test -f AGENTS.md            || echo "FAIL: no AGENTS.md"
test -f specs/STATUS.md      || echo "FAIL: no STATUS.md"
test -d .git                 || echo "FAIL: no git repo"

# Verify no pipeline phases ran (no feature branch created)
git branch | grep -q "feat/" && echo "FAIL: feature branch created" || echo "PASS: no feature branch"
```

## Smoke test (existing project)

```bash
# Use an existing project directory with AGENTS.md + git remote
hermes-panel init "Add user authentication system" ~/huat

# Verify constitution reflects audit
grep -q "strangle" specs/roadmap.md || echo "WARN: no strangle reference in roadmap"
```

## Exit code check

```bash
hermes-panel init "test" /tmp/nonexistent && echo "PASS: exit 0" || echo "FAIL: non-zero exit"
```

## Syntax check

```bash
python3 -c "compile(open('hermes-panel').read(), 'hermes-panel', 'exec')" && echo "PASS: syntax OK"
```
