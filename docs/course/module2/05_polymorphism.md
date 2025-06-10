# 2.5 Polymorphism in Python

Polymorphism, meaning "many forms," is a core concept in Object-Oriented Programming. It refers to the ability of different objects to respond to the same method call in their own specific ways. In simpler terms, it allows you to use a single interface (like a method name) to represent different underlying forms (implementations).

Polymorphism often works hand-in-hand with inheritance, but it's not strictly limited to it (e.g., duck typing).

**Key Ideas of Polymorphism:**

1.  **Same Interface, Different Behavior:** Objects of different classes can share the same method name, but the actual code executed when the method is called depends on the object's type.
2.  **Flexibility and Extensibility:** You can write generic code that works with objects of various types, as long as they implement the expected interface. This makes it easier to add new classes that conform to the interface without changing the existing generic code.

### Polymorphism with Class Inheritance (Method Overriding)

This is the most common way polymorphism is achieved. We've already seen it with method overriding in the inheritance section.

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def make_sound(self):
        raise NotImplementedError("Subclasses must implement this abstract method")

class Dog(Animal):
    def make_sound(self): # Overrides Animal's make_sound
        return f"{self.name} says Woof!"

class Cat(Animal):
    def make_sound(self): # Overrides Animal's make_sound
        return f"{self.name} says Meow!"

class Bird(Animal):
    def make_sound(self): # Overrides Animal's make_sound
        return f"{self.name} says Chirp!"

# Create a list of different Animal objects
animals = [
    Dog("Buddy"),
    Cat("Whiskers"),
    Bird("Sky"),
    Dog("Rex")
]

# Iterate and call the same method on different objects
# Polymorphism in action: animal.make_sound() behaves differently for each object type
for animal in animals:
    print(animal.make_sound())

# Expected Output:
# Buddy says Woof!
# Whiskers says Meow!
# Sky says Chirp!
# Rex says Woof!
```

In this example:
*   `Dog`, `Cat`, and `Bird` all inherit from `Animal`.
*   Each subclass provides its own implementation of the `make_sound()` method.
*   The `for` loop iterates through the `animals` list. For each `animal` object, `animal.make_sound()` is called.
*   Python automatically determines which version of `make_sound()` to execute based on the actual type of the `animal` object at runtime. This is polymorphism.

We can write a generic function that uses this polymorphic behavior:

```python
def animal_speaks(animal_object):
    # This function doesn't need to know the specific type of animal
    # as long as it has a make_sound() method.
    print(f"Listen: {animal_object.make_sound()}")

animal_speaks(Dog("Daisy"))    # Output: Listen: Daisy says Woof!
animal_speaks(Cat("Shadow"))   # Output: Listen: Shadow says Meow!
animal_speaks(Bird("Polly"))   # Output: Listen: Polly says Chirp!
```

### Polymorphism with Duck Typing

Python is a dynamically typed language, which leads to a concept often called "duck typing." The idea is: "If it walks like a duck and quacks like a duck, then it must be a duck."

In programming terms, if an object has the necessary methods and attributes that your code expects, it can be used in that context, regardless of its actual class or whether it inherits from a specific base class.

```python
class Car:
    def travel(self):
        print("Car is travelling on the road.")

class Bicycle:
    def travel(self):
        print("Bicycle is moving on the path.")

class Airplane:
    def fly(self): # Note: Different method name
        print("Airplane is flying in the sky.")

    def travel(self): # Adding the expected method
        print("Airplane is travelling through the air.")


# This function expects an object with a 'travel()' method
def start_journey(vehicle):
    # It doesn't care about the type of 'vehicle', only that it can 'travel()'
    vehicle.travel()

car = Car()
bike = Bicycle()
plane = Airplane()

start_journey(car)   # Output: Car is travelling on the road.
start_journey(bike)  # Output: Bicycle is moving on the path.
start_journey(plane) # Output: Airplane is travelling through theair.

# If we had an object without a travel() method:
# class Train:
#     def move_on_rails(self):
#         print("Train is moving on rails.")
#
# train = Train()
# start_journey(train) # This would raise an AttributeError because Train doesn't have a travel() method.
```
In this duck typing example:
*   `Car` and `Bicycle` (and `Airplane` after modification) are not related by inheritance.
*   However, they both implement a `travel()` method.
*   The `start_journey` function can work with any object that has a `travel()` method, demonstrating polymorphism without relying on a common base class.

### Polymorphism in Built-in Functions

Many of Python's built-in functions exhibit polymorphism. For example, the `len()` function can be used on various types of objects (strings, lists, dictionaries, tuples, etc.) that implement the `__len__()` special method.

```python
print(len("Hello"))      # Output: 5 (String)
print(len([1, 2, 3, 4])) # Output: 4 (List)
print(len({"a": 1, "b": 2})) # Output: 2 (Dictionary)

# The '+' operator also behaves polymorphically:
print(1 + 2)          # Output: 3 (Integer addition)
print("Hello" + " " + "World") # Output: Hello World (String concatenation)
print([1, 2] + [3, 4]) # Output: [1, 2, 3, 4] (List concatenation)
```
The `+` operator calls different internal methods (`__add__` for numbers, `__add__` for strings, `__add__` for lists) depending on the types of operands.

**Benefits of Polymorphism:**

*   **Simpler Code:** Allows you to write more generic and cleaner code that can operate on objects of different types.
*   **Flexibility:** Makes the system more flexible and easier to extend. New classes can be added that conform to an existing interface without modifying the code that uses the interface.
*   **Reduced Conditionals:** Avoids the need for long `if-elif-else` chains to check object types and call specific methods.

Polymorphism is a key enabler of writing robust, adaptable, and maintainable object-oriented software. It allows for treating objects of different classes in a uniform way if they share a common interface or behavior.
