from kubernetes import client, config
from kubernetes.stream import stream
from fastapi import UploadFile
from os import path
import base64


def upload_textfile_to_pod(api: client.CoreV1Api, name: str, file: UploadFile, destination_folder: str, problem_name: str):
    # encode as b64
    file_content = file.file.read()
    file_content = base64.b64encode(file_content)
    file_content = file_content.decode("utf-8")

    commands = ['/bin/sh']

    # upload tar file to pod
    resp = stream(api.connect_get_namespaced_pod_exec, name, "acadnet",
                  command=commands,
                  stdin=True, stdout=True, stderr=True, tty=True,
                  _preload_content=False)

    commands = [
        "pwd",
        "mkdir -p " + destination_folder + "/" + problem_name,
        "cd " + destination_folder + "/" + problem_name,
        "echo " + file_content + " | base64 -d > " + file.filename
    ]

    while resp.is_open():
        resp.update(timeout=1)
        # if resp.peek_stdout():
            # print("STDOUT: %s" % resp.read_stdout())
        # if resp.peek_stderr():
            # print("STDERR: %s" % resp.read_stderr())
        if commands:
            c = commands.pop(0)
            # print("Running command... %s\n" % c)
            resp.write_stdin(c + "\n")
        else:
            break

    resp.close()