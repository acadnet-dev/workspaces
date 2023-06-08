from fastapi import FastAPI, UploadFile, File
import uvicorn
import time
from uuid import uuid4
import os
from os import path
import yaml

from config import Config
from utils import upload_file_to_pod

from kubernetes import client, config

app_config = Config("config.json")
app = FastAPI()

class Workspace:
    def __init__(self, workspace_id):
        self.id = workspace_id
        self.pod_name = "vscode-server-" + self.id

    def add_file(self, file: UploadFile):
        with open(self.path + "/" + file.filename, "wb") as f:
            f.write(file.file.read())

    def create_pod(self):
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        with open(path.join(path.dirname(__file__), "vscode-server-deployment.yaml")) as f:
            pod = yaml.safe_load(f)

            pod_name = pod["metadata"]["name"] + "-" + self.id
            pod["metadata"]["name"] = pod_name

            resp = v1.create_namespaced_pod(
                body=pod, namespace="acadnet")
            print(f"Pod created with name {pod_name}")

        # wait for sandbox to start maxim 5 minutes (pod creation takes a while, even more if scaling up)
        # 5 minutes = 60 * 5 = 300 seconds (poll every 5 seconds 60 times)
        ok = False
        for i in range(60):
            pod_status = v1.read_namespaced_pod_status(pod_name, "acadnet")
            if pod_status.status.phase == "Running":
                ok = True
                break
            time.sleep(5)

        if not ok:
            raise Exception("Sandbox failed to start")
        
        self.pod_name = pod_name

    def get_pod_endpoint(self):
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        # if pod does not exist, return None
        try:
            status = v1.read_namespaced_pod_status(self.pod_name, "acadnet")

            if status.status.phase != "Running":
                return None

            return f"http://{status.status.pod_ip}:3000"
        except Exception as e:
            return None

    def add_file(self, file: UploadFile):
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        upload_file_to_pod(v1, self.pod_name, file, "/home/workspace/" + file.filename)    
    
# gets endpoint for workspace
@app.post("/workspace/get/")
async def create_workspace(id: str, files: list[UploadFile]):
    try:
        # create new workspace
        workspace = Workspace(id)

        # get pod endpoint
        endpoint = workspace.get_pod_endpoint()

        # if pod does not exist, create it
        if endpoint == None:
            # create pod
            workspace.create_pod()
            # add files to pod
            for file in files:
                workspace.add_file(file)
            # get pod endpoint
            endpoint = workspace.get_pod_endpoint()

        return {"endpoint": endpoint}
    except Exception as e:
        raise e
        return {"error": str(e)}

def run():
    uvicorn.run(app, host="0.0.0.0", port=app_config.port)

if __name__ == "__main__":
    run()