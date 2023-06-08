from kubernetes import client, config
from kubernetes.stream import stream
from fastapi import UploadFile
from os import path
import base64


def upload_textfile_to_pod(api: client.CoreV1Api, name: str, file: UploadFile, destination_folder: str):
    # encode as b64
    file_content = file.file.read()
    file_content = base64.b64encode(file_content)

    commands = []
    # echo b64 | base64 -d > file
    commands.append(f"echo {file_content} | base64 -d > {destination_folder}/{file.filename}")

    # upload tar file to pod
    resp = stream(api.connect_get_namespaced_pod_exec, name, "acadnet",
                  command=commands,
                  stdin=True, stdout=True, stderr=True, tty=False,
                  _preload_content=False)

    resp.close()

    # remove tar file
    # resp = stream(api.connect_get_namespaced_pod_exec, name, "acadnet",
    #               command=["rm", tar_file],
    #               stdin=True, stdout=True, stderr=True, tty=False,
    #               _preload_content=False)
    # resp.write_stdin(None)
    # print(resp.read_stdout())
    # print(resp.read_stderr())