def upload_file_to_pod(api,):
    # Copying file
    exec_command = ['tar', 'xvf', '-', '-C', '/']
    resp = stream(api.connect_get_namespaced_pod_exec, name, 'default',
                command=exec_command,
                stderr=True, stdin=True,
                stdout=True, tty=False,
                _preload_content=False)

    source_file = '/tmp/dash.tar'
    destination_file = '/tmp/sh'

    file = open(source_file, "rb")

    buffer = b''
    with open(source_file, "rb") as file:
        buffer += file.read()

    commands = []
    commands.append(buffer)

    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            print("STDOUT: %s" % resp.read_stdout())
        if resp.peek_stderr():
            print("STDERR: %s" % resp.read_stderr())
        if commands:
            c = commands.pop(0)
            #print("Running command... %s\n" % c)
            resp.write_stdin(c)
        else:
            break
    resp.close()