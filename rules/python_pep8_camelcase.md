# Python PEP8 with CamelCase Convention

## Overview
Follow PEP8 style guidelines for Python code with the exception of using camelCase for naming conventions.

## Naming Conventions

### Variables and Functions
- Use **camelCase** for variable names and function names
- Start with lowercase letter
- Examples:
  ```python
  userName = "John"
  totalCount = 42
  
  def getUserData():
      pass
  
  def calculateTotalPrice(items):
      pass
  ```

### Classes
- Use **PascalCase** (UpperCamelCase) for class names
- Example:
  ```python
  class UserProfile:
      pass
  
  class DatabaseConnection:
      pass
  ```

### Constants
- Use **UPPER_CASE_WITH_UNDERSCORES** for constants
- Example:
  ```python
  MAX_CONNECTIONS = 100
  API_TIMEOUT = 30
  DEFAULT_CONFIG_PATH = "/etc/config"
  ```

### Private Members
- Prefix with single underscore for internal use
- Use camelCase after the underscore
- Example:
  ```python
  class MyClass:
      def __init__(self):
          self._internalValue = 0
          self._configData = {}
      
      def _helperMethod(self):
          pass
  ```

## Code Formatting

### Indentation
- Use 4 spaces per indentation level
- Never mix tabs and spaces

### Line Length
- Limit lines to 79 characters for code
- Limit lines to 72 characters for comments and docstrings

### Imports
- Imports should be on separate lines
- Group imports: standard library, third-party, local application
- Example:
  ```python
  import os
  import sys
  
  import numpy as np
  import requests
  
  from myapp import myModule
  ```

### Whitespace
- Avoid extraneous whitespace
- Use spaces around operators
- No spaces inside parentheses, brackets, or braces
- Example:
  ```python
  # Good
  def myFunction(x, y):
      result = x + y
      return result
  
  # Bad
  def myFunction( x,y ):
      result=x+y
      return result
  ```

### Blank Lines
- Two blank lines between top-level functions and classes
- One blank line between methods in a class
- Use blank lines sparingly inside functions

## Documentation

### Docstrings
- Use triple quotes for docstrings
- Follow Google or NumPy docstring format
- Example:
  ```python
  def calculateAverage(numbers):
      """
      Calculate the average of a list of numbers.
      
      Args:
          numbers: List of numeric values
      
      Returns:
          float: The average of the numbers
      """
      return sum(numbers) / len(numbers)
  ```

### Comments
- Use inline comments sparingly
- Write comments as complete sentences
- Keep comments up to date with code changes

## Best Practices

### String Quotes
- Use double quotes for strings by default
- Use single quotes to avoid escaping
- Be consistent within a module

### Comparisons
- Use `is` and `is not` for None comparisons
- Use `isinstance()` for type checking
- Example:
  ```python
  if value is None:
      pass
  
  if isinstance(obj, MyClass):
      pass
  ```

### Boolean Comparisons
- Don't compare boolean values to True or False
- Example:
  ```python
  # Good
  if isActive:
      pass
  
  # Bad
  if isActive == True:
      pass
  ```

### List Comprehensions
- Use comprehensions for simple cases
- Use regular loops for complex logic
- Example:
  ```python
  # Good
  squaredNumbers = [x**2 for x in range(10)]
  
  # For complex logic, use regular loop
  processedData = []
  for item in items:
      if item.isValid():
          processed = item.process()
          if processed:
              processedData.append(processed)
  ```

## Error Handling

### Exceptions
- Be specific with exception types
- Use context managers where appropriate
- Example:
  ```python
  try:
      result = riskyOperation()
  except ValueError as e:
      logger.error(f"Invalid value: {e}")
  except IOError as e:
      logger.error(f"IO error: {e}")
  finally:
      cleanup()
  ```

## Type Hints

- Use type hints for function signatures
- Example:
  ```python
  def processData(inputData: List[str], maxItems: int = 10) -> Dict[str, Any]:
      """Process input data and return results."""
      result = {}
      for item in inputData[:maxItems]:
          result[item] = analyze(item)
      return result
  ```

## Tools and Linters

### Recommended Tools
- **Black** (with custom config for camelCase)
- **Flake8** for PEP8 compliance
- **MyPy** for type checking
- **isort** for import sorting

### Configuration
Create a `.flake8` config to allow camelCase:
```ini
[flake8]
max-line-length = 79
ignore = N802, N803, N806
```

## Summary

Follow PEP8 for all formatting and style rules, with the **key exception** of using camelCase for variables, functions, and method names instead of snake_case. This provides a consistent coding style while accommodating the camelCase preference.
