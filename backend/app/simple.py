from fastapi import FastAPI, UploadFile, File
import uvicorn

app = FastAPI(title="IntelliKYC API")

@app.get("/")
def read_root():
    return {"message": "IntelliKYC API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    return {
        "filename": file.filename, 
        "size": len(content),
        "content_type": file.content_type
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
