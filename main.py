from fastapi import FastAPI, UploadFile, File, Form
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId

app = FastAPI()
client = MongoClient("mongodb://localhost:27017")
db = client["collab_db"]
fs = GridFS(db)
projects = db["projects"]

@app.post("/projects/{project_id}/upload-file/")
async def upload_file(project_id: str, folder_path: str = Form(...), file: UploadFile = File(...)):

    file_id = fs.put(await file.read(), filename=file.filename, content_type=file.content_type)

    project = projects.find_one({"_id": project_id})

    if not project:
        return {"error": "Project not found"}

    def insert_file_in_folder(folders, path_parts):
        for folder in folders:
            if folder["name"] == path_parts[0]:
                if len(path_parts) == 1:
                    folder.setdefault("files", []).append({
                        "name": file.filename,
                        "type": file.content_type,
                        "file_id": str(file_id)
                    })
                else:
                    insert_file_in_folder(folder.setdefault("subfolders", []), path_parts[1:])

    insert_file_in_folder(project["folders"], folder_path.strip("/").split("/"))

    projects.replace_one({"_id": project_id}, project)

    return {"message": "File uploaded", "file_id": str(file_id)}
