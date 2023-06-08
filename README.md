# Workspaces

# What is a workspace exactly
* an entry in the database with a unique uuid describing a users workspace for a specific problem
* a folder on the server with the same uuid containing the problems statement and source code

## When user clicks on a problem to solve online
1. click solve online
2. check the database if the user already has a context for that problemId
3. if yes, redirect it to it
4. if no, call workspace manager to create a new one

## How does workspace creation work?
1. create a new workspace entry in the database
2. create a new folder on the server with the same uuid
3. upload the problem statement and source code to the folder


## How does workspace access work?
* user access is based on a url with the workspace uuid
* the workspace manager checks if the user is authenthicated and has access to the workspace
* if the user is not authenthicated, the workspace manager redirects to the login page
* the workspace manager becomes a proxy for the vscode server


## How does checking work?
* the vscode server has a custom extension that calls the web api to check the submission

## New idea
* use the current web app as proxy
* have a restricted api to launch new workspaces and proxy the traffic to their api