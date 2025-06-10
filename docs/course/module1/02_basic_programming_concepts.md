# 1.2 Basic Programming Concepts

Regardless of the programming language, there are some fundamental concepts that are common to all.

### Variables

A variable is like a container that stores a piece of information (data). You give a variable a name, and you can change the value it holds.

*Example (Python):*
```python
name = "Alice"  # Storing text (string)
age = 30       # Storing a whole number (integer)
price = 19.99  # Storing a number with a decimal (float)
is_student = True # Storing a truth value (boolean)
```

### Data Types

Data types define the kind of values a variable can hold and what operations can be performed on those values. Common data types include:

*   **Integer (`int`):** Whole numbers (e.g., -5, 0, 100).
*   **Float (`float`):** Numbers with a decimal point (e.g., 3.14, -0.5).
*   **String (`str`):** Text, enclosed in quotes (e.g., "hello", 'Python').
*   **Boolean (`bool`):** Represents truth values, either `True` or `False`.
*   **List (`list`):** An ordered collection of items (e.g., `[1, 2, 3]`, `['apple', 'banana']`).
*   **Dictionary (`dict`):** An unordered collection of key-value pairs (e.g., `{'name': 'Bob', 'age': 25}`).

### Control Flow

Control flow determines the order in which instructions are executed.

*   **Sequential:** Instructions are executed one after another, in the order they are written.
*   **Conditional (Selection):** Executes a block of code only if a certain condition is true.
    *   `if`, `elif` (else if), `else` statements.
    *Example (Python):*
    ```python
    if age >= 18:
        print("You are an adult.")
    else:
        print("You are a minor.")
    ```
*   **Loops (Repetition/Iteration):** Repeats a block of code multiple times.
    *   `for` loop: Iterates over a sequence (e.g., a list, a range of numbers).
    *   `while` loop: Repeats as long as a condition is true.
    *Example (Python `for` loop):*
    ```python
    fruits = ["apple", "banana", "cherry"]
    for fruit in fruits:
        print(fruit)
    ```
    *Example (Python `while` loop):*
    ```python
    count = 0
    while count < 5:
        print(count)
        count = count + 1 # or count += 1
    ```

### Functions

A function is a reusable block of code that performs a specific task. Functions help organize code, make it more readable, and avoid repetition.

*   **Defining a function:** Giving it a name and specifying the instructions it performs.
*   **Calling a function:** Executing the code within the function.
*   **Parameters/Arguments:** Input values that can be passed to a function.
*   **Return value:** The output or result that a function can send back.

*Example (Python):*
```python
# Defining a function
def greet(name):
    message = "Hello, " + name + "!"
    return message

# Calling the function
greeting = greet("Alice")
print(greeting)  # Output: Hello, Alice!
```
