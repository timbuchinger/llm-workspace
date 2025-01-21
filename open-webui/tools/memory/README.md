uvicorn server_script_name:app --reload

# Example usage of the API client
print(add_memory("This is a test memory.", ["test", "example"]))
print(retrieve_all())
print(search_memory("test"))
print(get_by_tag(["example"]))
print(delete_memory("This is a test memory."))