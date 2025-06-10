# 1.4 Setting Up Your Python Development Environment

To start writing and running Python code, you need to set up a development environment.

**1. Install Python:**

*   **Windows:**
    1.  Go to the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    2.  Download the latest stable installer for Windows.
    3.  Run the installer. **Important:** Check the box that says "Add Python to PATH" during installation. This makes it easier to run Python from the command line.
    4.  Verify installation: Open Command Prompt (cmd) and type `python --version` or `py --version`. You should see the installed Python version.
*   **macOS:**
    1.  Python usually comes pre-installed on macOS. To check, open Terminal and type `python3 --version`.
    2.  If it's not installed or you want the latest version, you can install it via:
        *   **Official Installer:** Download from [https://www.python.org/downloads/](https://www.python.org/downloads/).
        *   **Homebrew (recommended):** If you have Homebrew installed, open Terminal and run `brew install python3`.
    3.  Verify installation: In Terminal, type `python3 --version`.
*   **Linux:**
    1.  Python is usually pre-installed on most Linux distributions. To check, open Terminal and type `python3 --version`.
    2.  If not installed or for a specific version, use your distribution's package manager:
        *   **Debian/Ubuntu:** `sudo apt update && sudo apt install python3 python3-pip`
        *   **Fedora:** `sudo dnf install python3 python3-pip`
    3.  Verify installation: In Terminal, type `python3 --version`.

**2. Python Interpreter:**

The Python interpreter is what actually runs your Python code. You can use it in two ways:

*   **Interactive Mode:** Type `python` or `python3` in your terminal. This opens the Python REPL (Read-Eval-Print Loop), where you can type Python code directly and see immediate results. Great for testing small snippets.
    ```bash
    $ python3
    Python 3.9.7 (...) on ...
    Type "help", "copyright", "credits" or "license" for more information.
    >>> print("Hello from interactive mode!")
    Hello from interactive mode!
    >>> x = 5
    >>> x * 2
    10
    >>> exit()
    ```
*   **Running Python Scripts:** Save your Python code in a file with a `.py` extension (e.g., `my_script.py`). Then run it from the terminal using `python3 my_script.py`.

**3. `pip` - The Python Package Installer:**

`pip` is the standard package manager for Python. It allows you to install and manage additional libraries and packages that are not part of the Python standard library.

*   `pip` is usually installed automatically with Python.
*   Verify installation: `pip --version` or `pip3 --version`.
*   **Common `pip` commands:**
    *   `pip install package_name`: Installs a package.
    *   `pip uninstall package_name`: Uninstalls a package.
    *   `pip list`: Lists installed packages.
    *   `pip freeze > requirements.txt`: Saves a list of installed packages and their versions to a file (good for sharing project dependencies).
    *   `pip install -r requirements.txt`: Installs packages from a `requirements.txt` file.

**4. Code Editors and Integrated Development Environments (IDEs):**

While you can write Python code in a simple text editor, using a code editor or IDE provides features like syntax highlighting, code completion, debugging tools, and project management, which significantly improve productivity.

*   **Recommended Code Editors/IDEs for Beginners:**
    *   **Visual Studio Code (VS Code):**
        *   Free, open-source, and highly popular.
        *   Excellent Python support through extensions (e.g., Microsoft's Python extension).
        *   Lightweight yet powerful.
        *   Download: [https://code.visualstudio.com/](https://code.visualstudio.com/)
    *   **PyCharm Community Edition:**
        *   A powerful IDE specifically designed for Python development.
        *   The Community Edition is free.
        *   Offers robust debugging, testing, and code analysis features.
        *   Download: [https://www.jetbrains.com/pycharm/download/](https://www.jetbrains.com/pycharm/download/)
    *   **Thonny:**
        *   A beginner-friendly Python IDE with a simple interface.
        *   Comes with Python built-in, so it's easy to get started.
        *   Good for learning the basics.
        *   Download: [https://thonny.org/](https://thonny.org/)

**5. Virtual Environments (Recommended):**

When working on different Python projects, they might have different library dependencies or versions. Virtual environments allow you to create isolated environments for each project, preventing conflicts.

*   Python's built-in module for creating virtual environments is `venv`.
*   **Creating a virtual environment:**
    ```bash
    # Navigate to your project directory
    cd my_project
    # Create a virtual environment named 'venv' (common practice)
    python3 -m venv venv
    ```
*   **Activating a virtual environment:**
    *   **Windows (cmd):** `venv\Scripts\activate.bat`
    *   **Windows (PowerShell):** `venv\Scripts\Activate.ps1` (You might need to set execution policy: `Set-ExecutionPolicy Unrestricted -Scope Process`)
    *   **macOS/Linux (bash/zsh):** `source venv/bin/activate`
    *   Once activated, your terminal prompt will usually change to indicate the active environment (e.g., `(venv) $`).
*   **Installing packages within the active environment:**
    ```bash
    (venv) $ pip install requests
    ```
    Packages installed in an active virtual environment are only available to that environment.
*   **Deactivating a virtual environment:**
    ```bash
    (venv) $ deactivate
    ```

This setup provides a solid foundation for your Python programming journey!
```
