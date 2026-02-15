# Emoji Collation Bug Fix

## Issue Summary
**Date Discovered:** February 14, 2026  
**Severity:** High - Production Bug  
**Affected Component:** Reactions system (emoji reactions on posts)

## The Problem

### Symptoms
When a user updated their reaction emoji from one type to another (e.g., ❤️ → 🔥), the GROUP BY query that counts reactions by emoji type was returning incorrect counts:
- Expected: `{'🔥': 1, '👍': 1}` (one fire, one thumbs up)
- Actual: `{'🔥': 2}` (both emojis counted as fire)

### Root Cause
The `reactions.emoji` column was using MySQL's `utf8mb4_unicode_ci` collation. This collation uses Unicode equivalence rules that can treat different emojis as "equivalent" for sorting and grouping purposes.

**Technical Details:**
- Unicode collations like `utf8mb4_unicode_ci` apply normalization and equivalence rules
- Some emoji variants, modifiers, or even different emojis can be considered "equivalent" under these rules
- This caused MySQL's `GROUP BY reactions.emoji` to incorrectly group different emojis together
- The COUNT was aggregating multiple distinct emojis as if they were the same emoji

### Evidence
```
=== DEBUG OUTPUT ===
Database rows for post 94:
  ID:43, User:46, Emoji:'🔥'  (bytes: f09f94a5)
  ID:44, User:47, Emoji:'👍'  (bytes: f09f918d)

GROUP BY result:
  [('🔥', 2)]  ← WRONG! Should be [('🔥', 1), ('👍', 1)]
```

## The Solution

Changed the `emoji` column collation from `utf8mb4_unicode_ci` to `utf8mb4_bin`:

```sql
ALTER TABLE reactions 
MODIFY COLUMN emoji VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL;
```

### Why This Works
- `utf8mb4_bin` performs **byte-by-byte comparison**
- No Unicode normalization or equivalence rules are applied
- Each unique emoji byte sequence is treated as distinct
- GROUP BY now correctly groups emojis by their exact byte values

## Files Updated

1. **schema.sql** - Updated table definition with correct collation
2. **EMOJI_COLLATION_BUG.md** - This documentation file
3. **reaction.py** - Model uses the corrected schema

## Migration Guide

### For Existing Deployments
Run this migration on your production database:

```bash
mysql -u root -p pulse_db < fix_emoji_collation.sql
```

Or manually:
```sql
ALTER TABLE reactions 
MODIFY COLUMN emoji VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL;
```

### For New Deployments
No action needed - the corrected schema.sql already includes `utf8mb4_bin` collation.

## Testing

After applying the fix, verify with:

```sql
-- Check the collation
SHOW FULL COLUMNS FROM reactions WHERE Field = 'emoji';
-- Should show: utf8mb4_bin

-- Test GROUP BY behavior
INSERT INTO reactions (post_id, user_id, emoji) VALUES (999, 1, '🔥'), (999, 2, '👍');
SELECT emoji, COUNT(*) FROM reactions WHERE post_id = 999 GROUP BY emoji;
-- Should return two rows: ('🔥', 1) and ('👍', 1)
```

Run the automated test suite:
```bash
python test_reactions.py
# Should show: Total: 26 | Passed: 26 | Failed: 0 ✅
```

## Lessons Learned

1. **Always use binary collation for emoji columns** - Unicode collations can cause unexpected grouping behavior
2. **Test edge cases thoroughly** - The bug only appeared when updating reactions, not when adding them
3. **MySQL collation matters** - The default `utf8mb4_unicode_ci` is good for text but problematic for emojis
4. **Debug at the database level** - SQL query logging revealed the issue was in MySQL's GROUP BY, not in the application code

## Related Issues

- None (first occurrence)

## References

- MySQL Documentation: [Character Sets and Collations](https://dev.mysql.com/doc/refman/8.0/en/charset-unicode-sets.html)
- Stack Overflow: "MySQL GROUP BY with emoji columns"
- Unicode Standard: Collation vs Binary Comparison

---

**Status:** ✅ RESOLVED  
**Resolution Date:** February 14, 2026  
**Resolution Verified:** All 26 reaction tests passing
