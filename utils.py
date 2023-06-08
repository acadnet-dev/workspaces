from kubernetes import client, config
from kubernetes.stream import stream
from fastapi import UploadFile
from os import path

def upload_file_to_pod(api: client.CoreV1Api, name: str, file: UploadFile, destination: str):
    # get file name
    file_name = path.basename(file.filename)

    # create tar file
    tar_file = f"/tmp/{file_name}.tar"
    with open(tar_file, "wb") as f:
        f.write(file.file.read())

    # upload tar file to pod
    resp = stream(api.connect_get_namespaced_pod_exec, name, "acadnet",
                  command=["tar", "xvf", "-", "-C", destination],
                  stdin=True, stdout=True, stderr=True, tty=False,
                  _preload_content=False)

    commands = []
    with open(tar_file, "rb") as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            commands.append(data)

    
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

    # remove tar file
    # resp = stream(api.connect_get_namespaced_pod_exec, name, "acadnet",
    #               command=["rm", tar_file],
    #               stdin=True, stdout=True, stderr=True, tty=False,
    #               _preload_content=False)
    # resp.write_stdin(None)
    # print(resp.read_stdout())
    # print(resp.read_stderr())