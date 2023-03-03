# ChatAPI Server Module: GPT-J-6B

The `ChatAPI` server module for providing API service and running instance of [GPT-J-6B](https://github.com/kingoflolz/mesh-transformer-jax).

# Source

Files:
```
chatapi-gpt-j-6b.py
```

## chatapi-gpt-j-6b.py

### Requirement

```bash
python -m pip install torch transformers
```

### First Running

In the first running, the program will download the `GPT-J-6B` model from the Internet (about 25.5 GB). The model will be cached under `./.cache/`.

### Quick Start

And running with:
```bash
python3 chatapi-gpt-j-6b.py
```

When you see:
```bash
[Info <time>]: Loaded.
[Info <time>]: Running...
```
That represents the prepare work has been done.

Now, you can send a request by save a file into the `requests` folder (will be craete at python work dictory):
```bash
echo 'I like oranges. How about you?' > requests/1.request #Filename must ends with ".request".
```
After the program finished work, the request file will be delete and a new file with extname ".back" which including the result of your request will be create:
```bash
cat requests/1.back
```

### Exit Program

You can send `Ctrl+C` key as normal.

Or you can create a file named `quit.flag` into `flags` folder:
```bash
touch flags/quit.flag
```
If the program detects the flag file (**the detect work is after generate text**), the program will quit.

### Get Status Info

Or you can create a file named `status.flag` into `flags` folder:
```bash
touch flags/status.flag
```
And you will get the status info:
```bash
cat flags/status.back
```

**In fact, the `Status` value will always be `running` (** because the detect work is after generate text**).**

# Reference

```
@misc{gpt-j,
  author = {Wang, Ben and Komatsuzaki, Aran},
  title = {{GPT-J-6B: A 6 Billion Parameter Autoregressive Language Model}},
  howpublished = {\url{https://github.com/kingoflolz/mesh-transformer-jax}},
  year = 2021,
  month = May
}
```

---

View this repository on [GitHub](https://github.com/Orange23333/chatapi-server-module-gptj6b)
