uvicorn server:app --reload

# Example usage of the API client

```python
import client
print(client.add_memory("This is a test memory.", ["test", "example"]))
print(client.retrieve_all())
print(client.search_memory("test"))
print(client.get_by_tag(["example"]))
print(client.delete_memory("This is a test memory."))
```
