# 2.2 Classes and Objects in Python

In OOP, a **class** is a blueprint or template for creating objects. An **object** is an instance of a class.

Think of a class like a cookie cutter, and objects as the cookies created with that cutter. The cutter defines the shape and properties of the cookies, while each cookie is an individual instance with its own specific characteristics (e.g., some might have chocolate chips, others might have sprinkles, but they all share the same basic shape).

### Defining a Class

In Python, you define a class using the `class` keyword, followed by the class name (conventionally in CamelCase).

```python
class Dog:
    # Class attribute (shared by all instances of the class)
    species = "Canis familiaris"

    # Initializer / Constructor method
    def __init__(self, name, age, breed):
        # Instance attributes (specific to each object)
        self.name = name
        self.age = age
        self.breed = breed
        self.is_sleeping = False # Default value

    # Instance method
    def bark(self):
        return f"{self.name} says Woof!"

    # Another instance method
    def describe(self):
        return f"{self.name} is a {self.age}-year-old {self.breed}."

    def sleep(self):
        self.is_sleeping = True
        return f"{self.name} is now sleeping."

    def wake_up(self):
        if self.is_sleeping:
            self.is_sleeping = False
            return f"{self.name} just woke up."
        return f"{self.name} is already awake."
```

**Key Components of a Class Definition:**

*   **`class Dog:`**: This line declares a new class named `Dog`.
*   **`species = "Canis familiaris"`**: This is a **class attribute**. It's shared by all objects (instances) created from this class. You can access it using `Dog.species`.
*   **`__init__(self, name, age, breed)`**: This is a special method called the **initializer** or **constructor**.
    *   It's automatically called when you create a new object of the class.
    *   The `self` parameter is a reference to the newly created instance of the class. It's always the first parameter in instance methods.
    *   `name`, `age`, and `breed` are parameters that you pass when creating a `Dog` object.
    *   Inside `__init__`, `self.name = name`, `self.age = age`, and `self.breed = breed` create **instance attributes**. These attributes store data that is unique to each `Dog` object.
*   **`bark(self)`, `describe(self)`, `sleep(self)`, `wake_up(self)`**: These are **instance methods**. They define the behaviors or actions that objects of the class can perform.
    *   They always take `self` as their first parameter, allowing them to access and modify the object's instance attributes.

### Creating Objects (Instantiation)

Once you have a class, you can create objects (instances) from it. This process is called **instantiation**.

```python
# Creating Dog objects (instances of the Dog class)
dog1 = Dog("Buddy", 3, "Golden Retriever")
dog2 = Dog("Lucy", 5, "Poodle")
dog3 = Dog("Max", 1, "German Shepherd")

# Accessing instance attributes
print(f"{dog1.name} is a {dog1.breed}.") # Output: Buddy is a Golden Retriever.
print(f"{dog2.name} is {dog2.age} years old.") # Output: Lucy is 5 years old.

# Calling instance methods
print(dog1.bark())  # Output: Buddy says Woof!
print(dog2.describe()) # Output: Lucy is a 5-year-old Poodle.
print(dog3.sleep()) # Output: Max is now sleeping.
print(dog3.is_sleeping) # Output: True
print(dog3.wake_up()) # Output: Max just woke up.

# Accessing class attributes
print(f"All dogs belong to the species: {Dog.species}") # Output: All dogs belong to the species: Canis familiaris
print(f"{dog1.name} also belongs to: {dog1.species}") # Instance can also access class attributes
```

### `self` Keyword

The `self` keyword is crucial in Python OOP. It represents the instance of the class that a method is being called on.
*   When you call `dog1.bark()`, Python automatically passes `dog1` as the `self` argument to the `bark` method.
*   This allows methods to access and manipulate the specific data (attributes) associated with that particular instance.

### Example: Bank Account Class

Here's another example to illustrate classes and objects:

```python
class BankAccount:
    def __init__(self, account_holder, initial_balance=0):
        self.account_holder = account_holder
        self.balance = initial_balance
        print(f"Account for {self.account_holder} created with balance: ${self.balance:.2f}")

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            print(f"Deposited ${amount:.2f}. New balance: ${self.balance:.2f}")
        else:
            print("Deposit amount must be positive.")

    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            print(f"Withdrew ${amount:.2f}. New balance: ${self.balance:.2f}")
        elif amount > self.balance:
            print("Insufficient funds.")
        else:
            print("Withdrawal amount must be positive.")

    def get_balance(self):
        print(f"Current balance for {self.account_holder}: ${self.balance:.2f}")
        return self.balance

# Creating BankAccount objects
account1 = BankAccount("Alice", 1000)
account2 = BankAccount("Bob") # Uses default initial_balance

# Interacting with objects
account1.deposit(500)
account1.withdraw(200)
account1.get_balance()

account2.deposit(150)
account2.withdraw(200) # Insufficient funds
account2.get_balance()
```

Classes and objects are the fundamental building blocks of object-oriented programming. They allow you to structure your code in a way that is modular, reusable, and closely models real-world concepts.
