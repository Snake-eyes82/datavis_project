# Save this as test_odfpy_import.py
print("Script started.")

print("Attempting to import odfpy...")
try:
    import odfpy
    print("Successfully imported odfpy!")
except ModuleNotFoundError:
    print("ModuleNotFoundError: odfpy was not found.")
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")