# 2.6 Abstraction in Python

Abstraction is one of the core principles of Object-Oriented Programming (OOP). It focuses on **hiding complex implementation details** from the user and **showing only the essential features** or functionalities of an object or system.

Think of a remote control for a TV. You interact with simple buttons like "power," "volume up," "channel down." You don't need to know the complex electronics and circuitry working inside the remote or the TV to use it. The remote provides an abstraction layer.

**Core Ideas of Abstraction:**

1.  **Simplification:** Reduces complexity by hiding unnecessary details. Users interact with a simplified interface.
2.  **Focus on "What" not "How":** Users know *what* an object does, but not necessarily *how* it does it.
3.  **Generalization:** By abstracting common features, we can create more general and reusable components.

**Benefits of Abstraction:**

*   **Ease of Use:** Makes systems easier to use because users don't have to understand the intricate internal workings.
*   **Increased Security:** Hiding sensitive details can prevent unintended modifications or misuse.
*   **Better Maintainability:** Internal implementation can be changed (e.g., for optimization) without affecting how users interact with the system, as long as the abstract interface remains the same.
*   **Modularity:** Helps in breaking down a complex system into smaller, manageable, and independent components.

### Abstraction in Python

Abstraction in Python can be achieved in several ways:

1.  **Using Classes and Objects:**
    The very act of creating a class and its objects is a form of abstraction. You define attributes and methods that represent the essential features and behaviors of an entity, hiding the underlying implementation within the class methods.

    ```python
    class Car:
        def __init__(self, make, model):
            self.make = make
            self.model = model
            self.__is_engine_on = False # Internal detail

        def start_engine(self):
            # Complex logic for starting engine might be hidden here
            # e.g., check fuel, check battery, engage starter motor
            self.__is_engine_on = True
            print(f"{self.make} {self.model}'s engine started.")

        def stop_engine(self):
            self.__is_engine_on = False
            print(f"{self.make} {self.model}'s engine stopped.")

        def drive(self, destination):
            if self.__is_engine_on:
                print(f"Driving the {self.make} {self.model} to {destination}.")
            else:
                print(f"Cannot drive. The engine of {self.make} {self.model} is off.")

    # User interaction (Abstraction in action)
    my_car = Car("Toyota", "Camry")
    my_car.start_engine() # User calls start_engine(), doesn't need to know how it starts
    my_car.drive("work")
    my_car.stop_engine()

    # User doesn't (and shouldn't) directly interact with __is_engine_on
    # print(my_car.__is_engine_on) # Would cause an error or access mangled name
    ```
    Here, the user of the `Car` class interacts with `start_engine()`, `drive()`, and `stop_engine()`. The internal state `__is_engine_on` and the detailed steps to actually start an engine are abstracted away.

2.  **Abstract Base Classes (ABCs) using the `abc` module:**
    Python's `abc` module provides tools for creating Abstract Base Classes. ABCs define a common interface for a set of subclasses. They can declare abstract methods that subclasses *must* implement. This enforces that derived classes provide specific functionalities.

    *   **`@abstractmethod`**: A decorator to declare a method as abstract.
    *   An ABC cannot be instantiated directly if it contains abstract methods that haven't been implemented by a concrete subclass.

    ```python
    from abc import ABC, abstractmethod

    # Define an Abstract Base Class
    class Shape(ABC):
        def __init__(self, name):
            self.name = name

        @abstractmethod
        def area(self):
            """Return the area of the shape."""
            pass # Abstract methods typically don't have an implementation in the ABC

        @abstractmethod
        def perimeter(self):
            """Return the perimeter of the shape."""
            pass

        def describe(self): # Concrete method in an ABC
            print(f"This is a shape named {self.name}.")

    # Concrete subclass implementing the abstract methods
    class Rectangle(Shape):
        def __init__(self, name, width, height):
            super().__init__(name)
            self.width = width
            self.height = height

        def area(self): # Must implement this
            return self.width * self.height

        def perimeter(self): # Must implement this
            return 2 * (self.width + self.height)

    class Circle(Shape):
        def __init__(self, name, radius):
            super().__init__(name)
            self.radius = radius
            import math

        def area(self):
            return math.pi * self.radius ** 2

        def perimeter(self):
            return 2 * math.pi * self.radius

    # Attempting to instantiate an ABC with unimplemented abstract methods:
    # shape_obj = Shape("Generic Shape") # TypeError: Can't instantiate abstract class Shape
                                      # with abstract methods area, perimeter

    # Using concrete subclasses
    rectangle = Rectangle("MyRect", 10, 5)
    circle = Circle("MyCirc", 7)

    rectangle.describe() # Inherited concrete method
    print(f"Area of {rectangle.name}: {rectangle.area()}")
    print(f"Perimeter of {rectangle.name}: {rectangle.perimeter()}")

    circle.describe()
    print(f"Area of {circle.name}: {circle.area():.2f}")
    print(f"Perimeter of {circle.name}: {circle.perimeter():.2f}")

    # A function that works with any Shape (abstraction in action)
    def print_shape_details(s: Shape): # Type hinting s as Shape
        if not isinstance(s, Shape):
            print("Not a valid shape object")
            return
        s.describe()
        print(f"Its area is: {s.area():.2f}")
        print(f"Its perimeter is: {s.perimeter():.2f}")

    print_shape_details(rectangle)
    print_shape_details(circle)
    ```
    In this example:
    *   `Shape` is an ABC. It dictates that any concrete subclass *must* provide implementations for `area()` and `perimeter()`.
    *   The `print_shape_details` function can work with any object that is a `Shape` (i.e., adheres to the `Shape` interface/contract), without needing to know if it's a `Rectangle` or `Circle`. This is abstraction.

**Abstraction vs. Encapsulation:**

While related, they are distinct concepts:

*   **Encapsulation** is about bundling data (attributes) and methods that operate on that data into a single unit (class) and controlling access to that data (data hiding, often using private/protected conventions). It's more focused on the *implementation* and protection of an object's state.
*   **Abstraction** is about hiding the complex reality while exposing only the relevant parts. It's more focused on the *design* and providing a simplified interface to the user. An object's public methods are the abstraction it provides.

Encapsulation can be used to achieve abstraction. By hiding the internal attributes and exposing well-defined public methods, you provide an abstract view of the object.

Abstraction is a key principle for managing complexity in software development. It allows developers to focus on interactions between objects at a higher level without getting bogged down in the specific details of each object's implementation.
