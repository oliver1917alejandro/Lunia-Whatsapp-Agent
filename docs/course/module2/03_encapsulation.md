# 2.3 Encapsulation in Python

Encapsulation is one of the fundamental principles of Object-Oriented Programming (OOP). It refers to the bundling of data (attributes) and the methods that operate on that data within a single unit, called a class. More importantly, encapsulation involves restricting direct access to some of an object's components, which is known as **data hiding** or **information hiding**.

**Core Ideas of Encapsulation:**

1.  **Bundling:** Combining attributes and methods that manipulate them into a single object.
2.  **Data Hiding:** Protecting the internal state (attributes) of an object from unintended external modification. Access to the data is typically controlled through public methods (getters and setters).

**Benefits of Encapsulation:**

*   **Control:** You control how the data within an object is accessed and modified. This prevents accidental or improper changes to the object's state.
*   **Security:** The internal state of an object is hidden from the outside world, which can enhance the security and integrity of the data.
*   **Flexibility & Maintainability:** You can change the internal implementation of a class without affecting the code that uses the class, as long as the public interface (methods) remains the same. For example, you could change how a value is stored internally, but the getter method would still return it in the expected format.
*   **Simplicity:** It simplifies the use of objects, as users only need to interact with the public methods without worrying about the internal complexity.

### Access Modifiers in Python (Convention-based)

Unlike languages like Java or C++, Python doesn't have strict keywords like `public`, `private`, or `protected` to enforce access control. Instead, Python uses naming conventions to indicate the intended visibility of attributes and methods.

1.  **Public (`name`):**
    *   Attributes and methods are public by default.
    *   They can be accessed from anywhere, both inside and outside the class.
    *   Example: `self.name`, `my_object.my_method()`

2.  **Protected (Single Underscore Prefix: `_name`):**
    *   Indicates that an attribute or method is intended for internal use or by subclasses.
    *   It's a **convention**, and Python does not strictly enforce it. You can still access them from outside if you choose to (though it's generally bad practice).
    *   Treated as a hint to programmers: "This is not part of the public API, use with caution."
    *   Example: `self._balance`, `my_object._internal_calculation()`

3.  **Private (Double Underscore Prefix: `__name`):**
    *   Indicates that an attribute or method is strictly for internal use within the class.
    *   Python performs **name mangling** on attributes with a double underscore. This means the attribute name is changed to `_ClassName__attributeName` internally.
    *   This makes it harder (but not impossible) to access them directly from outside the class.
    *   Intended to prevent accidental overriding by subclasses and to strongly discourage external access.
    *   Example: `self.__secret_key`, `my_object._MyClass__private_method()` (mangled name)

### Example of Encapsulation

Let's consider a `BankAccount` class:

```python
class BankAccount:
    def __init__(self, account_holder, initial_balance=0):
        self.account_holder = account_holder  # Public attribute
        self._account_number = "ACC" + str(id(self))[-6:] # Protected attribute (convention)
        self.__balance = float(initial_balance)  # Private attribute (name mangled)

    def deposit(self, amount):
        if amount > 0:
            self.__balance += float(amount)
            print(f"Deposited ${amount:.2f}. New balance: ${self.__balance:.2f}")
        else:
            print("Deposit amount must be positive.")

    def withdraw(self, amount):
        if 0 < amount <= self.__balance:
            self.__balance -= float(amount)
            print(f"Withdrew ${amount:.2f}. New balance: ${self.__balance:.2f}")
        elif amount > self.__balance:
            print("Insufficient funds.")
        else:
            print("Withdrawal amount must be positive.")

    # Public method to get balance (Getter)
    def get_balance(self):
        print(f"Accessing balance for {self.account_holder}...")
        return self.__balance

    # Public method to set account holder (Setter - though not strictly necessary here)
    def set_account_holder(self, new_name):
        if isinstance(new_name, str) and len(new_name.strip()) > 0:
            self.account_holder = new_name.strip()
            print(f"Account holder name updated to: {self.account_holder}")
        else:
            print("Invalid account holder name.")

    def display_account_info(self):
        print(f"Account Holder: {self.account_holder}")
        print(f"Account Number (Protected): {self._account_number}")
        # We access __balance via a method or internally, not directly from outside
        print(f"Current Balance: ${self.get_balance():.2f}")


# Create an account
acc1 = BankAccount("Alice Wonderland", 1000)

# Accessing public attribute
print(f"Account Holder: {acc1.account_holder}") # Alice Wonderland

# Accessing protected attribute (possible, but not recommended directly)
print(f"Account Number: {acc1._account_number}") # e.g., ACC743856 (Output varies)

# Trying to access private attribute directly (will cause an AttributeError)
# print(acc1.__balance) # This will raise AttributeError: 'BankAccount' object has no attribute '__balance'

# Accessing private attribute via name mangling (possible, but strongly discouraged)
print(f"Mangaled Balance Access: {acc1._BankAccount__balance}") # Output: 1000.0

# Using public methods to interact with the data (preferred way)
acc1.deposit(500)    # Deposited $500.00. New balance: $1500.00
current_balance = acc1.get_balance() # Accessing balance for Alice...
print(f"My current balance is: ${current_balance:.2f}") # My current balance is: $1500.00

acc1.withdraw(2000)  # Insufficient funds.
acc1.withdraw(300)   # Withdrew $300.00. New balance: $1200.00

acc1.set_account_holder("Alice W.")
acc1.display_account_info()
```

**Explanation of the Example:**

*   `self.account_holder`: Public, can be accessed directly.
*   `self._account_number`: Protected. It's accessible, but the underscore suggests it's for internal use or subclasses.
*   `self.__balance`: Private. Attempting `acc1.__balance` directly from outside the class will fail. Python has mangled its name to `_BankAccount__balance`.
*   `get_balance()`: This is a **getter method**. It provides controlled read-only access to the `__balance` attribute.
*   `deposit()` and `withdraw()`: These methods control how the `__balance` is modified, ensuring it's done according to the bank's rules (e.g., positive deposits, sufficient funds for withdrawal).

By using encapsulation, we hide the `__balance` attribute and provide methods (`deposit`, `withdraw`, `get_balance`) to interact with it. This allows us to add validation or other logic within these methods if needed, without changing how external code uses the `BankAccount` object. If we later decide to store the balance in a different way (e.g., in cents as an integer to avoid floating-point issues), we can change the internal implementation of `__balance` and the methods, and the code using the class would not need to change as long as the method signatures remain the same.
