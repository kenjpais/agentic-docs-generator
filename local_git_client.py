"""Local Git client for reading repository data without GitHub API."""

import re
import subprocess
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from models import PullRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalGitClient:
    """Client for reading data from local git repositories."""

    def __init__(self, repo_path: str):
        """
        Initialize local git client.

        Args:
            repo_path: Path to local git repository
        """
        self.repo_path = Path(repo_path).resolve()
        if not self._is_git_repo():
            raise ValueError(f"Not a git repository: {repo_path}")

        logger.info(f"Initialized local git client for: {self.repo_path}")

    def _is_git_repo(self) -> bool:
        """Check if path is a valid git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def fetch_recent_commits(self, limit: int = 10, branch: str = 'HEAD') -> List[PullRequest]:
        """
        Fetch recent commits from local repository.

        Args:
            limit: Maximum number of commits to fetch
            branch: Branch to read from (default: HEAD)

        Returns:
            List of PullRequest objects created from commits
        """
        logger.info(f"Fetching {limit} recent commits from local repository")

        # Get commit hashes
        cmd = [
            'git', 'log',
            branch,
            '--pretty=format:%H',
            f'-{limit}'
        ]

        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        commit_hashes = result.stdout.strip().split('\n')
        commits = []

        for commit_hash in commit_hashes:
            commit_data = self._extract_commit_details(commit_hash)
            if commit_data:
                commits.append(commit_data)
                logger.info(f"Extracted commit {commit_hash[:8]}: {commit_data.title}")

        return commits

    def _extract_commit_details(self, commit_hash: str) -> Optional[PullRequest]:
        """Extract detailed information from a commit."""
        try:
            # Get commit metadata
            cmd = [
                'git', 'show',
                '--pretty=format:%H%n%s%n%b%n%ai',
                '--no-patch',
                commit_hash
            ]

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.strip().split('\n')
            if len(lines) < 3:
                return None

            full_hash = lines[0]
            subject = lines[1]

            # Find date line (last line that's a date)
            date_line = None
            body_lines = []
            for line in lines[2:]:
                # Check if this looks like a date
                if re.match(r'\d{4}-\d{2}-\d{2}', line):
                    date_line = line
                else:
                    body_lines.append(line)

            body = '\n'.join(body_lines).strip()

            # Parse date
            merged_at = None
            if date_line:
                try:
                    merged_at = datetime.strptime(date_line[:19], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass

            # Extract Jira ID
            jira_id = self._extract_jira_id_from_text(subject + '\n' + body)

            # Get changed files
            files_changed = self._get_changed_files(commit_hash)

            # Create PullRequest object (using commit hash as ID)
            pr = PullRequest(
                id=int(full_hash[:8], 16),  # Convert first 8 chars of hash to int
                number=int(full_hash[:6], 16),  # Shorter number
                title=subject,
                description=body,
                merged_at=merged_at,
                files_changed=files_changed,
                jira_id=jira_id
            )

            return pr

        except Exception as e:
            logger.error(f"Error extracting commit {commit_hash}: {e}")
            return None

    def _get_changed_files(self, commit_hash: str) -> List[dict]:
        """Get list of files changed in a commit."""
        try:
            # Get file stats
            cmd = [
                'git', 'show',
                '--stat=1000',  # Wide stat to avoid truncation
                '--format=',
                commit_hash
            ]

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            files = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip() or '|' not in line:
                    continue

                # Parse: " filename | 10 +++++-----"
                parts = line.split('|')
                if len(parts) != 2:
                    continue

                filename = parts[0].strip()
                stats = parts[1].strip()

                # Extract additions and deletions
                additions = stats.count('+')
                deletions = stats.count('-')

                # Get the actual diff for this file
                patch = self._get_file_patch(commit_hash, filename)

                files.append({
                    'filename': filename,
                    'additions': additions,
                    'deletions': deletions,
                    'changes': additions + deletions,
                    'patch': patch
                })

            return files

        except Exception as e:
            logger.error(f"Error getting changed files for {commit_hash}: {e}")
            return []

    def _get_file_patch(self, commit_hash: str, filename: str) -> str:
        """Get the patch/diff for a specific file in a commit."""
        try:
            cmd = [
                'git', 'show',
                f'{commit_hash}',
                '--',
                filename
            ]

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            # Limit patch size to avoid memory issues
            patch = result.stdout
            if len(patch) > 10000:
                patch = patch[:10000] + '\n... (truncated)'

            return patch

        except Exception as e:
            logger.debug(f"Could not get patch for {filename}: {e}")
            return ""

    def _extract_jira_id_from_text(self, text: str) -> Optional[str]:
        """
        Extract Jira ticket ID from text (commit message or body).

        Looks for patterns like: ABC-123, JIRA-456, OCPBUGS-789, etc.
        """
        # Common Jira ID pattern
        jira_pattern = r'\b([A-Z]{2,}[A-Z0-9]*-\d+)\b'

        match = re.search(jira_pattern, text)
        if match:
            return match.group(1)

        return None

    def get_repo_info(self) -> dict:
        """Get basic repository information."""
        try:
            # Get current branch
            branch_cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
            branch_result = subprocess.run(
                branch_cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = branch_result.stdout.strip()

            # Get remote URL
            remote_cmd = ['git', 'config', '--get', 'remote.origin.url']
            remote_result = subprocess.run(
                remote_cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            remote_url = remote_result.stdout.strip()

            # Extract repo owner and name from URL
            owner, name = self._parse_repo_from_url(remote_url)

            return {
                'path': str(self.repo_path),
                'branch': current_branch,
                'remote_url': remote_url,
                'owner': owner,
                'name': name
            }

        except Exception as e:
            logger.error(f"Error getting repo info: {e}")
            return {
                'path': str(self.repo_path),
                'branch': 'unknown',
                'remote_url': '',
                'owner': 'unknown',
                'name': self.repo_path.name
            }

    def _parse_repo_from_url(self, url: str) -> tuple:
        """Parse repository owner and name from git URL."""
        if not url:
            return 'unknown', self.repo_path.name

        # Handle GitHub URLs
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', url)
        if match:
            return match.group(1), match.group(2)

        # Fallback
        return 'unknown', self.repo_path.name
