import difflib
import os
import json

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import *
from actions.code_analysis_actions import CodeAnalysisActions
from actions.code_improvement_actions import CodeImprovementActions
from api_database.api_database import APIDatabase
from core.github_utils import clone_repository
from core.logging_utils import setup_logging, get_logger
from settings import load_settings, save_settings, SettingsDialog, SETTINGS_FILE, API_DATABASE_FILE
from tasks.code_analyzer import CodeAnalyzer
from tasks.code_improver import CodeImprover
from ui import UIMainWindow

# --- Setup Logging ---
setup_logging()
logger = get_logger(__name__)


class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    task_finished = pyqtSignal(str, str)

    def __init__(self, task, **kwargs):
        super().__init__()
        self.task = task
        self.kwargs = kwargs

    def run(self):
        try:
            if self.task == "clone_repo":
                self.progress_updated.emit(10)
                clone_repository(**self.kwargs)
                self.progress_updated.emit(100)
            elif self.task == "analyze_code":
                self.progress_updated.emit(10)
                self.kwargs.get("code_analyzer").analyze(self.kwargs.get("repo_path"))
                self.progress_updated.emit(100)
            elif self.task == "improve_class":
                self.progress_updated.emit(10)
                response = self.kwargs.get("code_improver").improve(self.kwargs.get("prompt"),
                                                                    self.kwargs.get("action"))
                self.progress_updated.emit(100)
                self.task_finished.emit(self.task, response)
            elif self.task == "summarize_api_doc":
                self.progress_updated.emit(10)
                summary = self.kwargs.get("code_analyzer").summarize_api_doc(self.kwargs.get("url"))
                self.progress_updated.emit(90)
                self.task_finished.emit(self.task, summary)
            elif self.task == "analyze_api_usage":
                self.progress_updated.emit(10)
                usage_patterns = self.kwargs.get("code_analyzer").analyze_api_usage(
                    self.kwargs.get("code_snippet"), self.kwargs.get("api_name")
                )
                self.progress_updated.emit(90)
                self.task_finished.emit(self.task, usage_patterns)
            elif self.task == "generate_test_cases":
                self.progress_updated.emit(10)
                test_cases = self.kwargs.get("code_improver").generate_test_cases(
                    self.kwargs.get("code"), self.kwargs.get("api_info")
                )
                self.progress_updated.emit(90)
                self.task_finished.emit(self.task, test_cases)
            else:
                self.task_finished.emit(self.task, "Error: Unknown task type")
        except Exception as e:
            self.task_finished.emit(self.task, f"Error: {e}")


class NewUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome!")
        self.setFixedSize(400, 300)

        # Create UI elements
        self.label = QLabel(
            "Welcome to the Gemini Code Improver!\n\n"
            "It seems this is your first time using the app.\n"
            "Would you like to start with a quick tutorial?"
        )
        self.tutorial_button = QPushButton("Yes, start tutorial")
        self.skip_button = QPushButton("Skip tutorial")

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.tutorial_button)
        layout.addWidget(self.skip_button)
        self.setLayout(layout)

        # Connect buttons
        self.tutorial_button.clicked.connect(self.accept)
        self.skip_button.clicked.connect(self.reject)


class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.code_improver = None
        self.code_analyzer = None
        self.api_db = None
        self.main_window = None
        self.settings = load_settings()
        self.setup_application()

    def setup_application(self):
        # Create instances of core components
        self.api_db = APIDatabase(API_DATABASE_FILE)
        self.code_analyzer = CodeAnalyzer(self.api_db, self)
        self.code_improver = CodeImprover(self.api_db, self)

        # Create main window
        self.main_window = MainAppWindow(
            self.api_db,
            self.code_analyzer,
            self.code_improver,
            self.settings
        )

        # --- Initialize CodeAnalyzer and CodeImprover after MainWindow creation ---
        self.code_analyzer = CodeAnalyzer(self.api_db, self)
        self.code_improver = CodeImprover(self.api_db, self)

        self.main_window.show()

        self.main_window.show()

        # Get API key if not set
        if not self.settings.get("api_key"):
            self.main_window.open_settings()


class MainAppWindow(UIMainWindow):
    def __init__(self, api_db, code_analyzer, code_improver, settings):
        super().__init__()

        # --- Check for First Time User ---
        if not os.path.exists(SETTINGS_FILE):
            self.show_new_user_dialog()

        # --- Components ---
        self.api_db = api_db
        self.code_analyzer = code_analyzer
        self.code_improver = code_improver
        self.settings = settings
        self.training_repos = self.settings.get("training_repos", [])
        # ... (Load other settings) ...

        # --- Data ---
        self.suggested_changes = None

        # --- Initialize Actions ---
        self.code_analysis_actions = CodeAnalysisActions(self, api_db, code_analyzer)
        self.code_improvement_actions = CodeImprovementActions(self, api_db, code_improver)

        # --- Connections ---
        self.add_repo_button.clicked.connect(self.code_analysis_actions.add_repository)
        self.remove_repo_button.clicked.connect(self.code_analysis_actions.remove_repository)
        self.analyze_button.clicked.connect(self.code_analysis_actions.analyze_user_repository)
        self.pull_changes_button.clicked.connect(self.code_analysis_actions.pull_changes)

        self.upgrade_api_button.clicked.connect(self.code_improvement_actions.upgrade_apis)
        self.switch_api_button.clicked.connect(self.code_improvement_actions.switch_api)
        self.general_improve_button.clicked.connect(self.code_improvement_actions.apply_general_improvements)
        self.apply_changes_button.clicked.connect(self.code_improvement_actions.apply_code_changes)

        settings_action = QAction("Preferences", self)
        settings_action.triggered.connect(self.open_settings)

        self.summarize_api_doc_action = QAction("Summarize API Documentation", self)
        self.summarize_api_doc_action.triggered.connect(
            self.code_analysis_actions.summarize_api_documentation
        )

        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(settings_action)
        analyze_menu = menu_bar.addMenu("Analyze")
        analyze_menu.addAction(self.summarize_api_doc_action)
        self.layout().setMenuBar(menu_bar)

    def show_new_user_dialog(self):
        dialog = NewUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.start_tutorial()

    def start_tutorial(self):
        QMessageBox.information(self, "Tutorial",
                                "Tutorial is under construction. For now, explore the menus and try adding a repository.")

    def closeEvent(self, event):
        """Save settings when the application closes."""
        self.settings["training_repos"] = self.training_repos
        # ... (Save other settings) ...
        save_settings(self.settings)
        event.accept()

    def open_settings(self):
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pass

    def start_background_task(self, task, **kwargs):
        """
        Starts a background task, updates the UI, and handles progress.
        """
        self.thread = WorkerThread(task, **kwargs)
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.task_finished.connect(self.handle_task_finished)

        task_descriptions = {
            "clone_repo": "Cloning repository...",
            "analyze_code": "Analyzing code...",
            "improve_class": "Improving code with Gemini...",
            "summarize_api_doc": "Summarizing API documentation...",
            "analyze_api_usage": "Analyzing API usage patterns...",
            "generate_test_cases": "Generating test cases...",
        }
        self.status_label.setText(task_descriptions.get(task, "Working..."))
        self.progress_bar.show()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def handle_task_finished(self, task_type, message):
        self.progress_bar.hide()
        QApplication.restoreOverrideCursor()
        self.status_label.setText("Ready")  # Reset status label

        if "Error" in message:
            self.show_error(message)
        else:
            if task_type == "clone_repo":
                self.show_message("Repository cloned successfully!")
            elif task_type == "analyze_code":
                class_list = self.code_analyzer.get_class_list()
                self.populate_class_dropdown(class_list)
            elif task_type == "improve_class":
                try:
                    response_data = json.loads(message)
                    improved_code = response_data.get("improved_code", "")
                    self.code_output.setPlainText(improved_code)

                    # --- Generate and Display Diff ---
                    self.suggested_changes = response_data.get("suggested_changes", {})
                    if self.suggested_changes:
                        self.apply_changes_button.setEnabled(True)
                        self.display_sugestion_diff(self.suggested_changes)
                    else:
                        self.apply_changes_button.setEnabled(False)
                        self.diff_view.setPlainText(
                            "No specific code changes to apply. Gemini may have provided general suggestions."
                        )

                except json.JSONDecodeError:
                    self.code_output.setPlainText(
                        "Error: Invalid response format from Gemini. Ensure it returns valid JSON with 'improved_code' and 'suggested_changes' keys."
                    )
                    self.apply_changes_button.setEnabled(False)
            elif task_type == "summarize_api_doc":
                self.code_output.setPlainText(message)  # Display the summary
            elif task_type == "analyze_api_usage":
                self.code_output.setPlainText(message)  # Display usage patterns
            elif task_type == "generate_test_cases":
                self.code_output.setPlainText(message)  # Display test cases

    def display_diff(self, diff_text):
        """Displays the given diff in the diff_view."""
        self.diff_view.setPlainText(diff_text)
        self.diff_view.setFont(QFont("Courier New", 10))

    def display_suggestion_diff(self, suggested_changes):
        diff_output = []
        for file_path, new_content in suggested_changes.items():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    original_content = f.read()
                diff = difflib.unified_diff(
                    original_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    lineterm='',
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}"
                )
                diff_output.append("".join(diff))
            except FileNotFoundError:
                self.show_error(f"File not found: {file_path}")
                return  # Stop processing diffs if a file is not found

        self.diff_view.setPlainText("\n".join(diff_output))
        self.diff_view.setFont(QFont("Courier New", 10))  # Set a monospaced font for better readability

    def populate_class_dropdown(self, class_list):
        self.class_dropdown.clear()
        self.class_dropdown.addItems(class_list.strip().split("\n"))

    def show_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def show_message(self, message):
        QMessageBox.information(self, "Information", message)
