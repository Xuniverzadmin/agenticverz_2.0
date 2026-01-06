#!/usr/bin/env python3
"""
AOS Configuration Verification Script
Validates all configuration files before deployment.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent


class ConfigValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passes: List[str] = []

    def validate_env_file(self, path: Path, required_vars: List[str]) -> bool:
        """Validate environment file"""
        if not path.exists():
            self.errors.append(f"Missing env file: {path}")
            return False

        content = path.read_text()
        vars_found = set()

        for line in content.split("\n"):
            if "=" in line and not line.startswith("#"):
                var = line.split("=")[0].strip()
                vars_found.add(var)

        missing = set(required_vars) - vars_found
        if missing:
            self.errors.append(f"Missing vars in {path.name}: {missing}")
            return False

        self.passes.append(f"Env file valid: {path.name}")
        return True

    def validate_no_localhost(self, path: Path) -> bool:
        """Check production configs don't have localhost"""
        if not path.exists():
            return True

        content = path.read_text()
        localhost_patterns = [r"localhost", r"127\.0\.0\.1", r"0\.0\.0\.0"]

        for pattern in localhost_patterns:
            if re.search(pattern, content):
                # Only warn if it's a production file
                if "production" in str(path).lower():
                    self.warnings.append(
                        f"Found localhost in production config: {path.name}"
                    )
                    return False

        return True

    def validate_no_secrets(self, path: Path) -> bool:
        """Check no hardcoded secrets"""
        if not path.exists():
            return True

        content = path.read_text()
        secret_patterns = [
            (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub token"),
            (r"hvs\.[a-zA-Z0-9]{20,}", "Vault token"),
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
        ]

        for pattern, name in secret_patterns:
            if re.search(pattern, content):
                self.errors.append(f"Possible {name} found in: {path.name}")
                return False

        return True

    def validate_apache_config(self, path: Path) -> bool:
        """Validate Apache config structure"""
        if not path.exists():
            self.errors.append(f"Missing Apache config: {path}")
            return False

        content = path.read_text()

        required_directives = [
            "ServerName",
            "SSLEngine",
            "ProxyPass",
            "DocumentRoot",
        ]

        for directive in required_directives:
            if directive not in content:
                self.errors.append(f"Missing directive '{directive}' in Apache config")
                return False

        # Check for security headers
        security_headers = [
            "X-Frame-Options",
            "X-XSS-Protection",
            "X-Content-Type-Options",
            "Strict-Transport-Security",
        ]

        for header in security_headers:
            if header not in content:
                self.warnings.append(f"Missing security header: {header}")

        self.passes.append("Apache config structure valid")
        return True

    def validate_console_build(self) -> bool:
        """Validate console is built"""
        dist_path = PROJECT_ROOT / "website/app-shell/dist"
        if not dist_path.exists():
            self.errors.append("Console not built - run 'npm run build'")
            return False

        index_html = dist_path / "index.html"
        if not index_html.exists():
            self.errors.append("Missing index.html in dist")
            return False

        assets_dir = dist_path / "assets"
        if not assets_dir.exists() or not list(assets_dir.iterdir()):
            self.errors.append("Missing or empty assets directory")
            return False

        self.passes.append("Console build valid")
        return True

    def validate_backend_cors(self) -> bool:
        """Check backend CORS configuration"""
        main_py = PROJECT_ROOT / "backend/app/main.py"
        if not main_py.exists():
            self.errors.append("Missing backend main.py")
            return False

        content = main_py.read_text()

        if 'allow_origins=["*"]' in content:
            self.warnings.append("CORS allows all origins - restrict in production")

        if "CORSMiddleware" not in content:
            self.errors.append("Missing CORS middleware")
            return False

        self.passes.append("Backend CORS configured")
        return True

    def run_all(self) -> Tuple[int, int, int]:
        """Run all validations"""
        print("=" * 60)
        print("AOS CONFIGURATION VALIDATION")
        print("=" * 60)
        print()

        # Console env files
        self.validate_env_file(
            PROJECT_ROOT / "website/app-shell/.env.production",
            ["VITE_API_BASE", "VITE_APP_NAME"],
        )

        # No localhost in production
        self.validate_no_localhost(PROJECT_ROOT / "website/app-shell/.env.production")

        # Apache config
        self.validate_apache_config(
            PROJECT_ROOT / "scripts/deploy/apache/agenticverz.com.conf"
        )

        # Console build
        self.validate_console_build()

        # Backend CORS
        self.validate_backend_cors()

        # No secrets
        for pattern in ["**/*.env*", "**/*.conf"]:
            for path in PROJECT_ROOT.glob(pattern):
                if ".git" not in str(path):
                    self.validate_no_secrets(path)

        # Print results
        print("✅ PASSED:")
        for p in self.passes:
            print(f"   {p}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for w in self.warnings:
                print(f"   {w}")

        if self.errors:
            print("\n❌ ERRORS:")
            for e in self.errors:
                print(f"   {e}")

        print()
        print("=" * 60)
        print(
            f"Results: {len(self.passes)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors"
        )
        print("=" * 60)

        return len(self.passes), len(self.warnings), len(self.errors)


def main():
    validator = ConfigValidator()
    passed, warnings, errors = validator.run_all()
    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()
