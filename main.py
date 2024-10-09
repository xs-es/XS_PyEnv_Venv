import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QComboBox, QTextEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal

# Thread for running commands without freezing the GUI
class CommandRunner(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
        stdout, stderr = process.communicate()
        if stdout:
            self.output_signal.emit(stdout)
        if stderr:
            self.output_signal.emit(f"Error: {stderr}")
        process.wait()

class PyEnvManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Python Venv Manager')

        # Main layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Python Version Dropdown
        self.python_version_label = QLabel("Python Version:")
        self.layout.addWidget(self.python_version_label)

        self.python_version_dropdown = QComboBox(self)
        self.layout.addWidget(self.python_version_dropdown)

        self.update_versions()

        # Package input and button
        self.package_input = QLineEdit(self, placeholderText="Enter package name")
        self.layout.addWidget(self.package_input)

        self.search_button = QPushButton('Search Package', self)
        self.search_button.clicked.connect(self.search_package)
        self.layout.addWidget(self.search_button)

        # Install button
        self.install_button = QPushButton('Install in Virtual Environment', self)
        self.install_button.clicked.connect(self.install_venv)
        self.layout.addWidget(self.install_button)

        # Console output
        self.console_output = QTextEdit(self)
        self.layout.addWidget(self.console_output)

        # Set console output to read-only and enable HTML formatting
        self.console_output.setReadOnly(True)
        self.console_output.setAcceptRichText(True)

    def update_versions(self):
        try:
            result = subprocess.run(['pyenv', 'versions'], stdout=subprocess.PIPE, text=True, check=True)
            versions = result.stdout.splitlines()
            for version in versions:
                self.python_version_dropdown.addItem(version.strip())
        except FileNotFoundError:
            print("Error: 'pyenv' command not found. Make sure pyenv is installed and in your PATH.")
            # Optionally, you can set a default state for your UI here
        except subprocess.CalledProcessError:
            print("Error: 'pyenv versions' command failed to execute.")
            # Handle the error appropriately

    def search_package(self):
        package_name = self.package_input.text()
        python_version = self.python_version_dropdown.currentText().strip()
        if package_name and python_version:
            # Use pyenv to run pip with the selected Python version
            command = f'pyenv exec python -m pip show {package_name}'
            self.run_command(command)

    def install_venv(self):
        python_version = self.python_version_dropdown.currentText().strip()
        package_name = self.package_input.text().strip()
        if python_version and package_name:
            command = f'pyenv virtualenv {python_version} myenv && pyenv activate myenv && pip install {package_name}'
            self.run_command(command)

    def run_command(self, command):
        self.console_output.append(f'Running: {command}')
        self.command_runner = CommandRunner(command)
        self.command_runner.output_signal.connect(self.update_console)
        self.command_runner.start()

    def update_console(self, output):
        if output.startswith("Error:"):
            self.console_output.append(output)
        else:
            # Split the output into lines and format each line
            lines = output.strip().split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    self.console_output.append(f"<b>{key.strip()}:</b> {value.strip()}")
                else:
                    self.console_output.append(line)
        
        # Scroll to the bottom of the console output
        self.console_output.verticalScrollBar().setValue(
            self.console_output.verticalScrollBar().maximum()
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PyEnvManager()
    window.show()
    sys.exit(app.exec_())
