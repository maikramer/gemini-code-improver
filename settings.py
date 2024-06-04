import os
import json
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)

# --- Settings ---
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS_FILE = "default_settings.json"
API_DATABASE_FILE = "api_data.db"


class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.settings = settings

        # --- API Key ---
        self.api_key_label = QLabel("Gemini API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.settings.get("api_key", ""))

        # --- Train on Changed Files ---
        self.train_on_changed_checkbox = QCheckBox("Train only on changed files")
        self.train_on_changed_checkbox.setChecked(self.settings.get("train_on_changed", False))

        # --- Temperature ---
        self.temperature_label = QLabel("Temperature (0.0 - 1.0):")
        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 1.0)
        self.temperature_spinbox.setSingleStep(0.1)
        self.temperature_spinbox.setValue(self.settings.get("temperature", 0.7))

        # --- Max Output Tokens ---
        self.max_tokens_label = QLabel("Max Output Tokens:")
        self.max_tokens_spinbox = QSpinBox()
        self.max_tokens_spinbox.setRange(1, 8192)
        self.max_tokens_spinbox.setValue(self.settings.get("max_output_tokens", 500))

        # --- Buttons ---
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        # --- Layout ---
        layout = QVBoxLayout()
        layout.addWidget(self.api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.train_on_changed_checkbox)
        layout.addWidget(self.temperature_label)
        layout.addWidget(self.temperature_spinbox)
        layout.addWidget(self.max_tokens_label)
        layout.addWidget(self.max_tokens_spinbox)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save_settings(self):
        self.settings["api_key"] = self.api_key_input.text()
        self.settings["train_on_changed"] = self.train_on_changed_checkbox.isChecked()
        self.settings["temperature"] = self.temperature_spinbox.value()
        self.settings["max_output_tokens"] = self.max_tokens_spinbox.value()
        save_settings(self.settings)
        self.accept()


def load_settings():
    """Load settings from JSON file."""
    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}  # Initialize with an empty dictionary if the file is not found
    return settings


def save_settings(settings):
    """Save settings to JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)