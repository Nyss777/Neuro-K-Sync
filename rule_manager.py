"""Rule management for metadata customization."""

import re
from typing import Final

from song_metadata import MetadataFields, SongMetadata


class RuleManager:
    """Utility class for managing and applying metadata rules."""

    COL_MAP: Final = {
        MetadataFields.UI_TITLE: MetadataFields.TITLE,
        MetadataFields.UI_ARTIST: MetadataFields.ARTIST,
        MetadataFields.UI_COVER_ARTIST: MetadataFields.COVER_ARTIST,
        MetadataFields.UI_VERSION: MetadataFields.VERSION,
        MetadataFields.UI_DISC: MetadataFields.DISC,
        MetadataFields.UI_TRACK: MetadataFields.TRACK,
        MetadataFields.UI_DATE: MetadataFields.DATE,
        MetadataFields.UI_COMMENT: MetadataFields.COMMENT,
        MetadataFields.UI_SPECIAL: MetadataFields.SPECIAL,
        MetadataFields.UI_FILE: MetadataFields.FILE,
    }

    @staticmethod
    def group_rules_by_logic(rules: list[dict[str, str]]) -> list[list[dict]]:
        """Group rules into logical blocks based on AND/OR operators."""
        if not rules:
            return []

        blocks = []
        current_block = []

        for i, rule in enumerate(rules):
            if i == 0:
                current_block.append(rule)
                continue
            logic = rule.get("logic", "AND")
            if logic == "AND":
                current_block.append(rule)
            else:
                if current_block:
                    blocks.append(current_block)
                current_block = [rule]
        if current_block:
            blocks.append(current_block)
        return blocks

    @staticmethod
    def eval_rule_block(
        rule_block: list[dict[str, str]],
        metadata: SongMetadata,
    ) -> bool:
        """Evaluate a block of rules with AND logic (all rules in block must match)."""
        if not rule_block:
            return False
        return all(RuleManager.eval_single_rule(rule, metadata) for rule in rule_block)

    @staticmethod
    def eval_single_rule(rule: dict[str, str], metadata: SongMetadata) -> bool:
        """Evaluate a single rule."""
        field = rule.get("if_field", "")
        op = rule.get("if_operator", "")
        val = rule.get("if_value", "")

        actual = metadata.get(field)

        if op == "is":
            return actual == val
        if op == "contains":
            return val in actual
        if op == "starts with":
            return actual.startswith(val)
        if op == "ends with":
            return actual.endswith(val)
        if op == "is empty":
            return actual == ""
        if op == "is not empty":
            return actual != ""
        if op == "is latest version":
            return metadata.is_latest
        if op == "is not latest version":
            return not metadata.is_latest
        return False

    @staticmethod
    def apply_template(template: str, metadata: SongMetadata) -> str:
        """Apply template with field values."""
        if not template:
            return ""
        try:
            return re.sub(r"\{([^}]+)\}", lambda m: metadata.get(m.group(1)), template)
        except Exception:
            return ""

    @staticmethod
    def apply_rules_list(rules: list[dict[str, str]], metadata: SongMetadata) -> str:
        """Apply rules list to field values with AND/OR grouping."""
        if not rules:
            return ""
        rule_blocks = RuleManager.group_rules_by_logic(rules)
        for block in rule_blocks:
            if RuleManager.eval_rule_block(block, metadata):
                template = block[-1].get("then_template", "")
                result = RuleManager.apply_template(template, metadata)
                if result.strip():
                    return result
        return ""
