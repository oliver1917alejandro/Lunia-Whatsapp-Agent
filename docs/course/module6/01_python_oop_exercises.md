# Module 6: Practical Exercises and Project Setup

## 6.1 Python and OOP Exercises

These exercises are designed to reinforce the Python and Object-Oriented Programming concepts from Modules 1 and 2.

**Exercise 1: Simple Calculator Class**

1.  Create a Python class called `Calculator`.
2.  The `__init__` method doesn't need to do much for now, maybe just print "Calculator created!".
3.  Implement the following instance methods:
    *   `add(self, num1, num2)`: Returns the sum of `num1` and `num2`.
    *   `subtract(self, num1, num2)`: Returns the difference.
    *   `multiply(self, num1, num2)`: Returns the product.
    *   `divide(self, num1, num2)`: Returns the division result. Handle the case where `num2` is zero (e.g., print an error message and return `None` or raise an exception).
4.  Create an instance of your `Calculator` class.
5.  Test each method with various numbers and print the results.

**Exercise 2: Personal Library**

1.  Define a class `Book` with attributes:
    *   `title` (string)
    *   `author` (string)
    *   `isbn` (string)
    *   `is_borrowed` (boolean, defaults to `False`)
2.  The `__init__` method should accept `title`, `author`, and `isbn` as arguments.
3.  Add a method `display_info(self)` that prints the book's details in a readable format.
4.  Add methods `borrow_book(self)` and `return_book(self)` that change the `is_borrowed` status and print a message indicating the action. Ensure a book cannot be borrowed if it's already borrowed, and cannot be returned if it's not borrowed.

5.  Define another class `Library`.
6.  The `Library` class should have an attribute `books` (a list, initialized as empty in `__init__`).
7.  Implement the following methods for the `Library` class:
    *   `add_book(self, book_object)`: Adds a `Book` object to the `books` list.
    *   `find_book_by_title(self, title)`: Searches for a book by its title in the `books` list and returns the `Book` object if found, otherwise `None`.
    *   `display_all_books(self)`: Iterates through all books in the library and calls their `display_info()` method.
    *   `borrow_book_by_title(self, title)`: Finds the book by title and calls its `borrow_book()` method.
    *   `return_book_by_title(self, title)`: Finds the book by title and calls its `return_book()` method.

8.  Create a few `Book` objects.
9.  Create a `Library` object.
10. Add the books to the library.
11. Test finding books, displaying all books, borrowing, and returning books.

**Exercise 3: Simple Inheritance - Shapes**
(Refer to the `Shape` example in Module 2 Section 2.6 on Abstraction if needed, but try to build this focusing on basic inheritance first).

1.  Create a base class `Shape` with:
    *   An `__init__` method that takes a `name` (e.g., "Circle", "Rectangle").
    *   A method `area(self)` that prints "Cannot calculate area for a generic shape." and returns 0.
    *   A method `perimeter(self)` that prints "Cannot calculate perimeter for a generic shape." and returns 0.
    *   A method `describe(self)` that prints "This is a shape named [name]."
2.  Create a subclass `Circle` that inherits from `Shape`:
    *   Its `__init__` should take `name` and `radius`. Call the parent's `__init__`.
    *   Override the `area(self)` method to calculate and return the area of a circle (π * r^2). Use `math.pi`.
    *   Override the `perimeter(self)` method to calculate and return the circumference (2 * π * r).
3.  Create a subclass `Rectangle` that inherits from `Shape`:
    *   Its `__init__` should take `name`, `width`, and `height`. Call the parent's `__init__`.
    *   Override the `area(self)` method to calculate and return the area of a rectangle (width * height).
    *   Override the `perimeter(self)` method to calculate and return the perimeter (2 * (width + height)).
4.  Create instances of `Circle` and `Rectangle`.
5.  Call their `describe()`, `area()`, and `perimeter()` methods.
6.  Create a list containing these shape objects. Iterate through the list and call the `describe()` and `area()` methods for each shape (demonstrating polymorphism).
