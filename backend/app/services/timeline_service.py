from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from app.services.local_repository_service import repository_service


class TimelineService:
    def generate(self) -> List[Dict[str, Any]]:
        """Generate a sequential timeline of project events."""
        events: List[Dict[str, Any]] = []

        # 1. Add initialization event
        events.append({
            "date": datetime(2023, 1, 1, tzinfo=timezone.utc).isoformat(),
            "event": "Project Repository Initialized",
            "source": "System",
        })

        # 2. Add local upload events
        upload_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
        if upload_dir.exists():
            for f in upload_dir.iterdir():
                if f.is_file():
                    stat = f.stat()
                    events.append({
                        "date": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                        "event": f"Document uploaded: {f.name}",
                        "source": "Upload System",
                    })

        # 3. Add README milestone event if present (max one entry)
        repo_files = repository_service.get_files()
        readme_found = any(
            f.get("name", "").lower() == "readme.md" for f in repo_files
        )
        if readme_found:
            events.append({
                "date": datetime.now(timezone.utc).isoformat(),
                "event": "README Milestone Updated",
                "source": "Repository",
            })

        # Sort ascending by date
        events.sort(key=lambda x: x["date"])
        return events

    async def generate_with_github(self) -> List[Dict[str, Any]]:
        """Extend local timeline events with live GitHub commit history."""
        events = self.generate()
        try:
            from app.services.github_service import github_service

            commits = await github_service.get_commits()
        except Exception:
            return events

        for commit in commits or []:
            payload = commit.get("commit") or {}
            committer = payload.get("committer") or {}
            date = committer.get("date") or (payload.get("author") or {}).get("date")
            if not date:
                continue
            message = (payload.get("message") or "Commit").split("\n")[0][:80]
            events.append(
                {
                    "date": date,
                    "event": message,
                    "source": "GitHub Commit",
                    "author": committer.get("name") or (payload.get("author") or {}).get("name"),
                }
            )

        events.sort(key=lambda x: x["date"])
        return events


timeline_service = TimelineService()
