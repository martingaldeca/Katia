c = get_config()  # noqa
c.InteractiveShellApp.exec_lines = [
    "%autoreload 2",
]
c.InteractiveShellApp.extensions = ["autoreload"]
