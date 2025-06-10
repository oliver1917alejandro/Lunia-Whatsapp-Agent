# 2.4 Inheritance in Python

Inheritance is a powerful feature in Object-Oriented Programming (OOP) that allows you to create a new class (the **child class** or **derived class**) that inherits attributes and methods from an existing class (the **parent class**, **base class**, or **superclass**).

The child class can reuse the code from the parent class, extend its functionality, and also override specific methods of the parent class. This promotes code reusability and establishes a hierarchical relationship between classes.

**Core Concepts:**

*   **"Is-A" Relationship:** Inheritance models an "is-a" relationship. For example, a `Dog` *is an* `Animal`. A `Car` *is a* `Vehicle`.
*   **Code Reusability:** Common attributes and methods can be defined in a base class and reused by multiple derived classes.
*   **Extensibility:** Derived classes can add new attributes and methods specific to their needs.
*   **Overriding:** Derived classes can provide a specific implementation for a method that is already defined in their parent class.

### Defining a Base Class and Derived Class

```python
# Base Class (Parent Class)
class Animal:
    def __init__(self, name, species):
        self.name = name
        self.species = species
        self.is_alive = True

    def make_sound(self):
        print("Some generic animal sound")

    def eat(self, food):
        print(f"{self.name} the {self.species} is eating {food}.")

    def show_status(self):
        print(f"Name: {self.name}, Species: {self.species}, Alive: {self.is_alive}")

# Derived Class (Child Class)
class Dog(Animal): # Dog inherits from Animal
    def __init__(self, name, breed, age):
        # Call the __init__ of the parent class (Animal)
        super().__init__(name, species="Dog") # species is fixed for Dog
        self.breed = breed # Attribute specific to Dog
        self.age = age     # Attribute specific to Dog

    # Overriding the make_sound method from Animal
    def make_sound(self):
        print(f"{self.name} says Woof! Woof!")

    # Adding a new method specific to Dog
    def fetch(self, item):
        print(f"{self.name} the {self.breed} is fetching the {item}.")

    # Overriding show_status to include Dog-specific info
    def show_status(self):
        super().show_status() # Call parent's show_status
        print(f"Breed: {self.breed}, Age: {self.age}")


# Another Derived Class
class Cat(Animal):
    def __init__(self, name, color):
        super().__init__(name, species="Cat")
        self.color = color

    # Overriding make_sound
    def make_sound(self):
        print(f"{self.name} says Meow!")

    # New method for Cat
    def purr(self):
        print(f"{self.name} is purring...")

    def show_status(self):
        super().show_status()
        print(f"Color: {self.color}")

```

**Explanation:**

1.  **`class Animal:`**: This is the base class. It has common attributes (`name`, `species`, `is_alive`) and methods (`make_sound`, `eat`, `show_status`).
2.  **`class Dog(Animal):`**: This line defines the `Dog` class and specifies that it inherits from `Animal`. `Animal` is the parent class of `Dog`.
3.  **`super().__init__(name, species="Dog")`**:
    *   The `super()` function is used to call a method from the parent class.
    *   Here, `super().__init__(name, "Dog")` calls the `__init__` method of the `Animal` class. This is important to ensure that the parent class's initialization logic (like setting `self.name` and `self.species`) is executed.
    *   We pass `"Dog"` for the `species` because all instances of `Dog` will have this species.
4.  **`self.breed = breed` and `self.age = age`**: These are attributes specific to the `Dog` class.
5.  **`def make_sound(self): ...` in `Dog`**: This is **method overriding**. The `Dog` class provides its own version of the `make_sound` method. When `make_sound()` is called on a `Dog` object, this version will be executed, not the one in `Animal`.
6.  **`def fetch(self, item): ...`**: This is a new method added by the `Dog` class. It's not present in the `Animal` class.
7.  **`super().show_status()` in `Dog.show_status`**: This demonstrates how a child class can extend the parent's method by first calling the parent's version and then adding its own specific output.

### Using Inherited Classes

```python
# Create an Animal object (though often base classes are more abstract)
generic_animal = Animal("Creature", "Unknown")
generic_animal.make_sound()  # Output: Some generic animal sound
generic_animal.eat("food")   # Output: Creature the Unknown is eating food.
generic_animal.show_status()
# Name: Creature, Species: Unknown, Alive: True

print("-" * 20)

# Create a Dog object
my_dog = Dog("Buddy", "Golden Retriever", 3)
my_dog.make_sound()  # Output: Buddy says Woof! Woof! (Dog's version)
my_dog.eat("kibble") # Output: Buddy the Dog is eating kibble. (Inherited from Animal)
my_dog.fetch("ball") # Output: Buddy the Golden Retriever is fetching the ball. (Dog's own method)
my_dog.show_status()
# Name: Buddy, Species: Dog, Alive: True
# Breed: Golden Retriever, Age: 3

print("-" * 20)

# Create a Cat object
my_cat = Cat("Whiskers", "Gray")
my_cat.make_sound()  # Output: Whiskers says Meow! (Cat's version)
my_cat.eat("fish")   # Output: Whiskers the Cat is eating fish. (Inherited)
my_cat.purr()        # Output: Whiskers is purring... (Cat's own method)
my_cat.show_status()
# Name: Whiskers, Species: Cat, Alive: True
# Color: Gray
```

### Types of Inheritance

*   **Single Inheritance:** A class inherits from only one base class (as shown above).
*   **Multiple Inheritance:** A class can inherit from multiple base classes.
    ```python
    class A:
        def method_a(self): print("Method A")
    class B:
        def method_b(self): print("Method B")
    class C(A, B): # C inherits from both A and B
        pass

    obj_c = C()
    obj_c.method_a() # Output: Method A
    obj_c.method_b() # Output: Method B
    ```
    Multiple inheritance can be powerful but can also lead to complexity (e.g., the "Diamond Problem" if base classes have methods with the same name). Python has a Method Resolution Order (MRO) to handle this.
*   **Multilevel Inheritance:** A class inherits from a derived class, forming a chain.
    ```python
    class Grandparent:
        def greet_gp(self): print("Hello from Grandparent")
    class Parent(Grandparent):
        def greet_p(self): print("Hello from Parent")
    class Child(Parent):
        def greet_c(self): print("Hello from Child")

    ch = Child()
    ch.greet_gp() # Output: Hello from Grandparent
    ch.greet_p()  # Output: Hello from Parent
    ch.greet_c()  # Output: Hello from Child
    ```
*   **Hierarchical Inheritance:** Multiple derived classes inherit from a single base class (like `Dog` and `Cat` inheriting from `Animal`).

### `isinstance()` and `issubclass()`

Python provides built-in functions to check relationships between objects and classes:

*   **`isinstance(object, ClassInfo)`**: Returns `True` if the `object` is an instance of `ClassInfo` or an instance of a subclass of `ClassInfo`.
    ```python
    print(isinstance(my_dog, Dog))      # Output: True
    print(isinstance(my_dog, Animal))   # Output: True (Dog is a subclass of Animal)
    print(isinstance(my_dog, Cat))      # Output: False
    print(isinstance(generic_animal, Dog)) # Output: False
    ```
*   **`issubclass(class, ClassInfo)`**: Returns `True` if `class` is a subclass of `ClassInfo`.
    ```python
    print(issubclass(Dog, Animal))   # Output: True
    print(issubclass(Animal, Dog))   # Output: False
    print(issubclass(Cat, Animal))   # Output: True
    print(issubclass(Dog, Dog))      # Output: True (A class is considered a subclass of itself)
    ```

Inheritance is a cornerstone of OOP, enabling elegant and reusable code structures by defining relationships and sharing behavior between classes.
