import os
from pathlib import Path
from typing import Dict, List, Any
from fastapi import HTTPException

# We resolve the repository root dynamically. 
# Since this file is in backend/app/services, the project root is 4 levels up.
# Alternatively, allow overriding via environment variables.
DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPO_ROOT = Path(os.getenv("REPO_ROOT", DEFAULT_REPO_ROOT))

# Common directories and files to ignore during traversal
IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", 
    "dist", "build", ".idea", ".vscode", "coverage"
}
IGNORE_FILES = {".DS_Store", "Thumbs.db"}

# Basic extension to language mapping
EXTENSION_LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".txt": "Text",
    ".sh": "Shell Script",
    ".env": "Environment Variables",
    ".gitignore": "Git Ignore",
    ".lock": "Lockfile"
}

class RepositoryService:
    """Service to read and analyze local repository structure and files."""
    
    def _is_ignored(self, path: Path) -> bool:
        """Check if a path should be ignored based on its parts or name."""
        if path.name in IGNORE_DIRS or path.name in IGNORE_FILES:
            return True
        # Check all parent directories in the path
        for part in path.parts:
            if part in IGNORE_DIRS:
                return True
        return False

    def get_structure(self) -> Dict[str, Any]:
        """Recursively build the folder and file hierarchy of the repository."""
        if not REPO_ROOT.exists():
            raise HTTPException(status_code=404, detail="Repository root not found.")
        
        def build_tree(current_path: Path) -> Dict[str, Any]:
            if self._is_ignored(current_path):
                return {} # Return empty dict, which we will filter out
                
            tree: Dict[str, Any] = {
                "name": current_path.name,
                "type": "directory" if current_path.is_dir() else "file",
                "path": str(current_path.relative_to(REPO_ROOT).as_posix()),
            }
            
            if current_path.is_dir():
                tree["children"] = []
                try:
                    # Sort directories first, then files, both alphabetically
                    for child in sorted(current_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                        child_tree = build_tree(child)
                        if child_tree:  # If not ignored
                            tree["children"].append(child_tree)
                except PermissionError:
                    pass # Skip directories we don't have permission to read
            else:
                # Add file specific metadata
                tree["size_bytes"] = current_path.stat().st_size
                tree["extension"] = current_path.suffix.lower()
                
            return tree
            
        tree = build_tree(REPO_ROOT)
        # Manually fix the root node's path string and name if it's the project root
        tree["name"] = REPO_ROOT.name
        tree["path"] = "/"
        return tree

    def get_files(self) -> List[Dict[str, Any]]:
        """Get a flat list of all files in the repository."""
        if not REPO_ROOT.exists():
            raise HTTPException(status_code=404, detail="Repository root not found.")
            
        files_list = []
        try:
            for path in REPO_ROOT.rglob("*"):
                if path.is_file() and not self._is_ignored(path):
                    files_list.append({
                        "name": path.name,
                        "path": str(path.relative_to(REPO_ROOT).as_posix()),
                        "size_bytes": path.stat().st_size,
                        "extension": path.suffix.lower()
                    })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error scanning files: {str(e)}")
            
        return files_list

    def get_folders(self) -> List[Dict[str, Any]]:
        """Get a flat list of all folders in the repository."""
        if not REPO_ROOT.exists():
            raise HTTPException(status_code=404, detail="Repository root not found.")
            
        folders_list = []
        try:
            for path in REPO_ROOT.rglob("*"):
                if path.is_dir() and not self._is_ignored(path):
                    folders_list.append({
                        "name": path.name,
                        "path": str(path.relative_to(REPO_ROOT).as_posix()),
                    })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error scanning folders: {str(e)}")
            
        return folders_list

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate and return repository statistics."""
        files = self.get_files()
        folders = self.get_folders()
        
        total_size = 0
        extensions_count: Dict[str, int] = {}
        languages_count: Dict[str, int] = {}
        
        # Sort files by size in descending order to get the largest files
        sorted_files = sorted(files, key=lambda f: f["size_bytes"], reverse=True)
        largest_files = sorted_files[:10]
        
        for f in files:
            size = f["size_bytes"]
            ext = f["extension"] or "No Extension"
            
            total_size += size
            
            # Count extensions
            extensions_count[ext] = extensions_count.get(ext, 0) + 1
            
            # Map to programming language and count
            lang = EXTENSION_LANGUAGE_MAP.get(ext, "Other")
            languages_count[lang] = languages_count.get(lang, 0) + 1
            
        return {
            "total_folders": len(folders),
            "total_files": len(files),
            "total_size_bytes": total_size,
            "extensions": extensions_count,
            "languages": languages_count,
            "largest_files": largest_files
        }

repository_service = RepositoryService()
