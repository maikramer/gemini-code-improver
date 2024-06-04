import os
import subprocess
from urllib.parse import urlparse

from PyQt6.QtWidgets import QInputDialog

from core import get_logger

logger = get_logger(__name__)


class CodeAnalysisActions:
    def __init__(self, main_window, api_db, code_analyzer):
        self.main_window = main_window
        self.api_db = api_db
        self.code_analyzer = code_analyzer

    def add_repository(self):
        repo_url = self.main_window.add_repo_input.text()
        if not repo_url:
            self.main_window.show_error("Please enter a repository URL.")
            return

        # --- Basic URL Validation ---
        if not repo_url.startswith("https://github.com/"):
            self.main_window.show_error(
                "Invalid GitHub repository URL. "
                "Please enter a URL starting with 'https://github.com/'."
            )
            return

        self.main_window.training_repos.append(repo_url)
        self.main_window.repo_list.addItem(repo_url)
        self.main_window.add_repo_input.clear()

        try:
            self.main_window.start_background_task(
                "clone_repo",
                url=repo_url,
                local_path=f"./cloned_repos/{repo_url.split('/')[-1]}"
            )
        except Exception as e:
            logger.error(f"Error adding repository: {e}")
            self.main_window.show_error(f"Error adding repository: {e}")

    def remove_repository(self):
        selected_items = self.main_window.repo_list.selectedItems()
        if not selected_items:
            self.main_window.show_error("Please select a repository to remove.")
            return

        for item in selected_items:
            repo_url = item.text()
            self.main_window.training_repos.remove(repo_url)
            self.main_window.repo_list.takeItem(self.main_window.repo_list.row(item))

            # ... (Optional: Add code to remove the cloned repository) ...

    def analyze_user_repository(self):
        self.main_window.user_repo_path = self.main_window.user_repo_input.text()

        # ... (Validate user_repo_path) ...

        self.main_window.start_background_task(
            "analyze_code",
            repo_path=self.main_window.user_repo_path,
            code_analyzer=self.code_analyzer,
        )

    def pull_changes(self):
        selected_items = self.main_window.repo_list.selectedItems()
        if not selected_items:
            self.main_window.show_error("Please select repositories to pull changes from.")
            return

        for item in selected_items:
            repo_url = item.text()
            local_path = f"./cloned_repos/{repo_url.split('/')[-1]}"

            try:
                if os.path.exists(local_path):
                    self.update_repository(local_path)
                else:
                    self.main_window.show_error(f"Local repository not found: {local_path}")
            except Exception as e:
                self.main_window.show_error(f"Error pulling changes: {e}")

    def update_repository(self, local_path):
        """Updates the repository and displays the diff."""
        try:
            # Pull changes
            subprocess.check_output(["git", "-C", local_path, "pull"])

            # Get diff after pulling (to show what actually changed)
            diff_after = subprocess.check_output(
                ["git", "-C", local_path, "diff", "HEAD", "origin/main"]
            ).decode()

            self.main_window.show_message(f"Changes pulled successfully for {local_path}")
            self.main_window.display_sugestion_diff(diff_after)  # Pass the diff to the main window
            self.main_window.start_background_task("analyze_code", repo_path=local_path,
                                                   code_analyzer=self.code_analyzer)

        except subprocess.CalledProcessError as e:
            self.main_window.show_error(f"Error updating repository: {e.output.decode()}")
        except Exception as e:
            logger.error(f"Error updating repository: {e}")
            self.main_window.show_error(f"Error updating repository: {e}")

    def summarize_api_documentation(self):
        """
        Gets the API documentation URL from the user, summarizes it
        using Gemini, and displays the summary.
        """
        url, ok = QInputDialog.getText(
            self.main_window,
            "API Documentation URL",
            "Enter the URL of the API documentation:",
        )

        if ok and url:
            try:
                # (Simple URL validation)
                parsed_url = urlparse(url)
                if not all([parsed_url.scheme, parsed_url.netloc]):
                    raise ValueError("Invalid URL format.")

                self.main_window.start_background_task(
                    "summarize_api_doc",
                    url=url,
                    code_analyzer=self.code_analyzer,
                )
            except ValueError as e:
                self.main_window.show_error(str(e))
