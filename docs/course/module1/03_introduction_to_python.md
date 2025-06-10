# 1.3 Introduction to Python

Python is a popular, high-level, interpreted programming language known for its readability and versatility.

**Key Features of Python:**

*   **Easy to Learn and Read:** Simple syntax that resembles plain English.
*   **Interpreted:** Code is executed line by line, making debugging easier.
*   **Dynamically Typed:** You don't need to declare variable types explicitly.
*   **Extensive Standard Library:** Comes with many built-in modules and functions for common tasks.
*   **Large Community and Ecosystem:** Abundant libraries, frameworks, and resources available.
*   **Versatile:** Used in web development, data science, machine learning, artificial intelligence, scripting, automation, and more.

**Basic Python Syntax:**

*   **Comments:** Lines starting with `#` are ignored by the interpreter and are used for explanations.
    ```python
    # This is a comment
    name = "Python" # This is an inline comment
    ```
*   **Indentation:** Python uses indentation (whitespace at the beginning of a line) to define blocks of code (e.g., inside loops, functions, conditional statements). This is crucial for Python's structure.
    ```python
    if True:
        print("This is indented") # Correct
    print("This is not")

    # if True:
    # print("This will cause an IndentationError") # Incorrect
    ```
*   **Variables and Assignment:**
    ```python
    x = 10
    message = "Hello"
    ```
*   **Printing Output:**
    ```python
    print("Hello, World!")
    print(x)
    ```

**Common Built-in Functions:**

*   `print()`: Displays output to the console.
*   `input()`: Reads input from the user.
*   `len()`: Returns the length of an object (e.g., string, list).
*   `type()`: Returns the type of an object.
*   `int()`, `float()`, `str()`: Convert values to different data types.

*Example:*
```python
user_name = input("Enter your name: ")
print("Hello, " + user_name)
age_str = input("Enter your age: ")
age_int = int(age_str) # Convert string input to integer
print("Next year, you will be", age_int + 1)
```

**Common Libraries (Standard Library):**

*   **`math`:** For mathematical functions (e.g., `math.sqrt()`, `math.sin()`).
*   **`datetime`:** For working with dates and times.
*   **`json`:** For working with JSON data.
*   **`os`:** For interacting with the operating system (e.g., file operations).
*   **`random`:** For generating random numbers.

To use a library (or module, in Python terminology), you first need to `import` it:
```python
import math

print(math.sqrt(16)) # Output: 4.0

import random
print(random.randint(1, 10)) # Prints a random integer between 1 and 10
```
