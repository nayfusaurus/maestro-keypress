# Test Suite Refactoring Design

**Date:** 2026-02-11
**Status:** Approved
**Target:** Reduce test count from 387 to 287 tests (26% reduction, -100 tests)
**Philosophy:** Balanced - consolidate repetitive patterns, maintain semantic categories

## Problem Statement

The current test suite has 387 tests with significant redundancy:
- 47% redundancy in keymap tests (206 tests total)
- Individual note tests instead of parameterized tests
- Defensive tests checking types and internal structures
- Duplicate coverage across multiple test approaches

This causes:
- Slower test execution
- Higher maintenance burden
- Reduced signal-to-noise ratio in test output

## Goals

1. Reduce test count by ~26% (387 → 287 tests)
2. Maintain 100% code coverage
3. Improve maintainability with parameterized patterns
4. Faster test execution
5. No behavioral changes to production code

## Design

### Testing Philosophy

**Balanced approach:**
- Consolidate repetitive patterns (parameterized tests)
- Maintain semantic categories (mappings, boundaries, transpose, etc.)
- Remove defensive tests (type checking, internal structure validation)
- Keep all essential behavior tests

**What to remove:**
- Individual note tests (replace with parameterized)
- Return type validation tests
- Internal structure tests (dict keys, held_keys set)
- Redundant coverage (same logic tested multiple ways)

**What to keep:**
- Boundary tests (MIN_NOTE, MAX_NOTE, range edges)
- Core behavior tests (transpose, sharp handling, focus detection)
- Error handling tests
- Integration tests (all essential)

### Refactoring Pattern

**Example: test_keymap_drums.py (35 → 12 tests)**

**Before:**
```python
def test_note_60_maps_to_y(self):
    assert midi_note_to_key(60) == "y"

def test_note_61_maps_to_u(self):
    assert midi_note_to_key(61) == "u"

# ... 6 more individual tests
```

**After:**
```python
@pytest.mark.parametrize("note,key", [
    (60, "y"), (61, "u"), (62, "i"), (63, "o"),
    (64, "h"), (65, "j"), (66, "k"), (67, "l"),
])
def test_drum_mappings(note, key):
    assert midi_note_to_key(note) == key
```

**Removed from drums:**
- 8 individual note tests → 1 parameterized test (8 cases)
- 23 defensive tests (return types, integrity checks, layout validation)

**Kept in drums (12 tests):**
- 1 parameterized mapping test (8 cases)
- 2 constant tests (MIN_NOTE, MAX_NOTE)
- 3 boundary tests (range validation)
- 2 transpose tests (with/without)
- 4 out-of-range tests (below/above/None)

### File-by-File Breakdown

#### Keymap Tests (206 → 110 tests, -96 tests)

**test_keymap_drums.py: 35 → 12 tests**
- Consolidate 8 note tests → 1 parameterized
- Remove 23 defensive tests
- Keep 12 essential tests

**test_keymap_15_double.py: 60 → 25 tests**
- Consolidate 15 C4-B4 tests → 1 parameterized (15 cases)
- Consolidate 16 C5-C6 tests → 1 parameterized (16 cases)
- Consolidate 12 sharp tests → 2 parameterized (skip + snap)
- Remove 7 defensive tests
- Keep 25 essential tests (2 mapping, 2 sharp, 3 boundary, 4 transpose, 2 out-of-range)

**test_keymap_15_triple.py: 57 → 25 tests**
- Same structure as 15_double
- Consolidate 15 note tests → 1 parameterized
- Consolidate 12 sharp tests → 2 parameterized
- Remove 6 defensive tests
- Keep 25 essential tests

**test_keymap_wwm.py: 54 → 30 tests**
- Consolidate 22 mapping tests → 2 parameterized (no-shift + shift)
- Consolidate 8 modifier tests → 2 parameterized
- Remove 4 defensive tests
- Keep 30 essential tests (2 mapping, 2 modifier, 3 boundary, 4 transpose, 2 out-of-range)

**test_keymap.py (22-key): ~40 → 18 tests** (estimated)
- Consolidate 22 note tests → 1 parameterized
- Remove defensive tests
- Keep boundary, transpose, out-of-range tests

#### Core Module Tests (181 → 155 tests, -26 tests)

**test_parser.py: 45 → 35 tests**
- Consolidate 9 multi-tempo tests → 3 parameterized
- Consolidate 6 `get_midi_info()` tests → 2 parameterized
- Remove 6 defensive tests
- Keep 20 essential tests (file size, error handling, edge cases)

**test_player.py: 52 → 45 tests**
- Remove 5 defensive tests (state validation, held_keys structure)
- Remove 2 redundant threading tests
- Keep all critical tests:
  - Event building logic (12 tests)
  - Key press/release behavior (8 tests)
  - Focus detection (6 tests)
  - Cache invalidation (5 tests)
  - Other core behavior (14 tests)

**test_config.py: 28 → 25 tests**
- Remove 3 defensive tests (dict structure validation)
- Keep validation tests (already parameterized)
- Keep load/save tests
- Keep default behavior tests

**test_gui.py: 68 → 65 tests**
- Remove 3 internal state checks
- Keep all UI behavior tests

**test_main.py: 35 → 32 tests**
- Remove 2 mock verification tests
- Keep all integration points

**test_integration.py: 18 → 18 tests**
- No changes (all essential end-to-end scenarios)

### Summary Table

| File | Before | After | Reduction | Notes |
|------|--------|-------|-----------|-------|
| **Keymap Tests** | **206** | **110** | **-96** | **47% reduction** |
| test_keymap_drums.py | 35 | 12 | -23 | Pilot refactoring |
| test_keymap_15_double.py | 60 | 25 | -35 | Parameterized mappings + sharp |
| test_keymap_15_triple.py | 57 | 25 | -32 | Same pattern as 15_double |
| test_keymap_wwm.py | 54 | 30 | -24 | Parameterized with modifiers |
| test_keymap.py | ~40 | 18 | -22 | 22-key consolidation |
| **Core Tests** | **181** | **155** | **-26** | **14% reduction** |
| test_parser.py | 45 | 35 | -10 | Parameterized tempo/info |
| test_player.py | 52 | 45 | -7 | Remove defensive tests |
| test_config.py | 28 | 25 | -3 | Minimal consolidation |
| test_gui.py | 68 | 65 | -3 | Remove state checks |
| test_main.py | 35 | 32 | -3 | Remove mock verification |
| test_integration.py | 18 | 18 | 0 | All essential |
| **Total** | **387** | **287** | **-100** | **26% reduction** |

## Implementation Strategy

### Phase 1: Pilot (test_keymap_drums.py)
- Refactor drums first (35 → 12 tests)
- Validate pattern before broad application
- Verify: `uv run pytest tests/test_keymap_drums.py -v`

### Phase 2: Keymap Files (parallel-safe)
- Refactor test_keymap_15_double.py (60 → 25 tests)
- Refactor test_keymap_15_triple.py (57 → 25 tests)
- Refactor test_keymap_wwm.py (54 → 30 tests)
- Refactor test_keymap.py (40 → 18 tests)
- Independent files, can be done in parallel
- Verify after each: `uv run pytest tests/test_keymap*.py -v`

### Phase 3: Core Files (sequential)
- Refactor test_parser.py (45 → 35 tests)
- Refactor test_player.py (52 → 45 tests)
- Refactor test_config.py (28 → 25 tests)
- Verify after each: `uv run pytest tests/test_parser.py tests/test_player.py tests/test_config.py -v`

### Phase 4: GUI/Main (sequential)
- Refactor test_gui.py (68 → 65 tests)
- Refactor test_main.py (35 → 32 tests)
- Leave test_integration.py unchanged (18 tests, all essential)
- Verify after each: `uv run pytest tests/test_gui.py tests/test_main.py -v`

### Phase 5: Verification
- Run full suite: `uv run pytest -v`
- Verify: 287 tests passing (down from 387)
- Run CI checks: `uv run ruff check src/`, `uv run mypy src/maestro/`
- Verify coverage unchanged (if coverage tracking enabled)

### Safety Principles
- Refactor one file at a time
- Run tests after each file
- Commit after each successful file refactor
- If any test fails, stop and debug before continuing
- Never batch commits

## Success Criteria

✅ All 287 tests passing
✅ No behavioral changes (same code coverage)
✅ Faster test execution (fewer tests)
✅ More maintainable (parameterized patterns)
✅ CI pipeline passes (Ruff, mypy, pytest)

## Benefits

1. **Faster test execution:** 26% fewer tests to run
2. **Better maintainability:** Parameterized patterns easier to extend
3. **Clearer test output:** Less noise from redundant tests
4. **Easier debugging:** Semantic grouping makes failures easier to locate
5. **Lower CI costs:** Faster test runs = faster feedback

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Accidentally remove essential test | Review each removal, run coverage check |
| Break test behavior during refactor | Verify after each file, commit incrementally |
| Parameterized tests hide specific failures | Use descriptive test IDs in parametrize |
| Introduce flaky tests | Run full suite 3x before declaring success |

## Non-Goals

- Coverage increase (maintain current coverage)
- Production code changes (tests only)
- Test framework changes (stay with pytest)
- Adding new test categories
