"""Centralized permission engine with risk classification and fine-grained rules."""

from __future__ import annotations

import fnmatch
import json
import os
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import CONFIG_DIR


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PermissionAction(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


@dataclass
class PermissionRule:
    tool: str = "*"
    path: str = ""
    command: str = ""
    url: str = ""
    action: PermissionAction = PermissionAction.ASK
    reason: str = ""

    def matches(self, tool: str, args: dict) -> bool:
        if not fnmatch.fnmatch(tool, self.tool):
            return False
        if self.path:
            target = args.get("path", "")
            if target and not fnmatch.fnmatch(target, self.path):
                return False
        if self.command:
            cmd = args.get("command", "")
            if cmd and not fnmatch.fnmatch(cmd, self.command):
                return False
        if self.url:
            url = args.get("url", "")
            if url and not fnmatch.fnmatch(url, self.url):
                return False
        return True


PERMISSIONS_FILE = CONFIG_DIR / "permissions.json"

RISK_MAP = {
    "read": RiskLevel.SAFE,
    "list_dir": RiskLevel.SAFE,
    "glob": RiskLevel.SAFE,
    "grep": RiskLevel.SAFE,
    "search": RiskLevel.SAFE,
    "fetch": RiskLevel.LOW,
    "todo": RiskLevel.SAFE,
    "plan": RiskLevel.SAFE,
    "question": RiskLevel.SAFE,
    "skill": RiskLevel.SAFE,
    "lsp": RiskLevel.LOW,
    "edit": RiskLevel.MEDIUM,
    "patch": RiskLevel.MEDIUM,
    "write": RiskLevel.MEDIUM,
    "delete": RiskLevel.HIGH,
    "shell": RiskLevel.HIGH,
    "task": RiskLevel.HIGH,
    "execute": RiskLevel.CRITICAL,
}

DANGEROUS_PATTERNS = [
    "rm -rf", "rm -r /", "mkfs", ":(){ :|:& };:",
    "dd if=", "> /dev/sda", "chmod 777", "chown -R",
    "wget", "curl.*|sh", "eval ", "exec ",
    "sudo", "su -", "passwd", "shadow",
    "format", "fdisk", "mount",
]


class PermissionEngine:
    """Evaluates tool calls against permission rules and risk levels."""

    def __init__(self, policy: str = "balanced"):
        self.policy = policy
        self._rules: list[PermissionRule] = []
        self._session_overrides: dict[str, PermissionAction] = {}
        self._load()

    def _load(self):
        if PERMISSIONS_FILE.exists():
            try:
                data = json.loads(PERMISSIONS_FILE.read_text())
                for r in data.get("rules", []):
                    self._rules.append(PermissionRule(
                        tool=r.get("tool", "*"),
                        path=r.get("path", ""),
                        command=r.get("command", ""),
                        url=r.get("url", ""),
                        action=PermissionAction(r.get("action", "ask")),
                        reason=r.get("reason", ""),
                    ))
            except Exception:
                pass

        if not self._rules:
            self._rules = [
                PermissionRule(tool="read", action=PermissionAction.ALLOW),
                PermissionRule(tool="list_dir", action=PermissionAction.ALLOW),
                PermissionRule(tool="glob", action=PermissionAction.ALLOW),
                PermissionRule(tool="grep", action=PermissionAction.ALLOW),
                PermissionRule(tool="todo", action=PermissionAction.ALLOW),
                PermissionRule(tool="plan", action=PermissionAction.ALLOW),
                PermissionRule(tool="question", action=PermissionAction.ALLOW),
                PermissionRule(tool="skill", action=PermissionAction.ALLOW),
                PermissionRule(tool="search", action=PermissionAction.ALLOW),
                PermissionRule(tool="fetch", action=PermissionAction.ALLOW),
                PermissionRule(tool="lsp", action=PermissionAction.ALLOW),
                PermissionRule(tool="write", action=PermissionAction.ASK),
                PermissionRule(tool="edit", action=PermissionAction.ASK),
                PermissionRule(tool="patch", action=PermissionAction.ASK),
                PermissionRule(tool="delete", action=PermissionAction.ASK),
                PermissionRule(tool="shell", action=PermissionAction.ASK),
                PermissionRule(tool="task", action=PermissionAction.ASK),
                PermissionRule(tool="execute", action=PermissionAction.DENY),
            ]

    def save(self):
        PERMISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "rules": [
                {
                    "tool": r.tool,
                    "path": r.path,
                    "command": r.command,
                    "url": r.url,
                    "action": r.action.value,
                    "reason": r.reason,
                }
                for r in self._rules
            ]
        }
        PERMISSIONS_FILE.write_text(json.dumps(data, indent=2))

    def get_risk_level(self, tool: str) -> RiskLevel:
        return RISK_MAP.get(tool, RiskLevel.HIGH)

    def check(self, tool: str, args: dict, risk_level: Optional[RiskLevel] = None) -> PermissionAction:
        key = f"{tool}:{json.dumps(args, sort_keys=True)[:200]}"
        if key in self._session_overrides:
            return self._session_overrides[key]

        if self.policy == "permissive":
            risk = risk_level or self.get_risk_level(tool)
            if risk in (RiskLevel.SAFE, RiskLevel.LOW):
                return PermissionAction.ALLOW

        for rule in self._rules:
            if rule.matches(tool, args):
                return rule.action

        risk = risk_level or self.get_risk_level(tool)
        if risk == RiskLevel.SAFE:
            return PermissionAction.ALLOW
        if risk in (RiskLevel.LOW, RiskLevel.MEDIUM):
            return PermissionAction.ASK
        return PermissionAction.DENY

    def allow_once(self, tool: str, args: dict):
        key = f"{tool}:{json.dumps(args, sort_keys=True)[:200]}"
        self._session_overrides[key] = PermissionAction.ALLOW

    def always_allow(self, tool: str, args: dict):
        path_pattern = args.get("path", "")
        command_pattern = args.get("command", "")
        url_pattern = args.get("url", "")
        self._rules.insert(0, PermissionRule(
            tool=tool,
            path=path_pattern,
            command=command_pattern,
            url=url_pattern,
            action=PermissionAction.ALLOW,
        ))
        self.save()

    def deny(self, tool: str, args: dict):
        key = f"{tool}:{json.dumps(args, sort_keys=True)[:200]}"
        self._session_overrides[key] = PermissionAction.DENY

    def revoke(self, tool: str, path: str = "", command: str = ""):
        self._rules = [
            r for r in self._rules
            if not (r.tool == tool and r.path == path and r.command == command)
        ]
        self.save()

    def add_rule(self, rule: PermissionRule):
        self._rules.insert(0, rule)
        self.save()

    def is_command_dangerous(self, command: str) -> bool:
        cmd_lower = command.lower()
        return any(pattern in cmd_lower for pattern in DANGEROUS_PATTERNS)

    def describe_action(self, tool: str, args: dict) -> str:
        risk = self.get_risk_level(tool)
        if tool == "shell":
            cmd = args.get("command", "")
            if self.is_command_dangerous(cmd):
                return f"Execute potentially destructive command: {cmd[:80]}"
            return f"Execute shell command: {cmd[:80]}"
        if tool == "write":
            path = args.get("path", "")
            return f"Write to file: {path}"
        if tool == "edit":
            path = args.get("path", "")
            return f"Edit file: {path}"
        if tool == "patch":
            path = args.get("path", "")
            return f"Apply patch to: {path}"
        if tool == "delete":
            path = args.get("path", "")
            return f"Delete file: {path}"
        if tool == "task":
            desc = args.get("description", "")[:60]
            return f"Spawn sub-agent: {desc}"
        if tool == "execute":
            return "Execute controlled dispatcher"
        return f"Run {tool} [{risk.value} risk]"
