from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import time
from uuid import uuid4
import os
from os import path
import yaml

from config import Config
from utils import upload_textfile_to_pod

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
        v1 = client.CoreV1Api()

        # if pod does not exist, return None
        try:
            status = v1.read_namespaced_pod_status(self.pod_name, "acadnet")

            if status.status.phase != "Running":
                return None

            return f"http://{status.status.pod_ip}:3000"
        except Exception as e:
            return None

    def add_file(self, file: UploadFile, problem_name: str):
        v1 = client.CoreV1Api()

        upload_textfile_to_pod(v1, self.pod_name, file, "/home/workspace", problem_name)    
    
# creates and then returns the endpoint for workspace
@app.post("/workspace/create/")
async def create_workspace(id: str, problem_name: str, files: list[UploadFile]):
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
                workspace.add_file(file, problem_name)
            # get pod endpoint
            endpoint = workspace.get_pod_endpoint()

        return {"endpoint": endpoint}
    except Exception as e:
        raise e
        return {"error": str(e)}

# returns the endpoint for workspace if it exists
@app.get("/workspace/get/")
async def get_workspace(id: str):
    # create new workspace
    workspace = Workspace(id)

    # get pod endpoint
    endpoint = workspace.get_pod_endpoint()

    # if pod does not exist, return error
    if endpoint == None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return {"endpoint": endpoint}

def run():
    uvicorn.run(app, host="0.0.0.0", port=app_config.port)

if __name__ == "__main__":
    if app_config.is_development():
        config.load_kube_config('/home/dimi/.kube/config', context='do-fra1-acadnet-dev-k8s')
    else:
        config.load_incluster_config()
    run()