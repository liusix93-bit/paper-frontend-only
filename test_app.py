import sys
import os

class FakeFile:
    def __init__(self, path):
        self.name = path

class DummyProgress:
    def __call__(self, percent, desc=None):
        msg = f"[Progress] {percent}: {desc}"
        print(msg.encode('gbk', 'ignore').decode('gbk'))

# Import the module
import web_app_final

file_path = r"C:\桌面\标书\Inhibition of the Sp1 PI3K AKT signaling pathway exacerbates(1).pdf"
file_obj = FakeFile(file_path)

print("Starting test...")
try:
    generator = web_app_final.process_upload(file_obj, "刘", progress=DummyProgress())
    for status, preview, gallery in generator:
        print(f"\n--- STATUS UPDATE ---")
        print(f"Status Msg: {status}")
        if gallery:
            print(f"Gallery Images: {len(gallery)}")
            for img in gallery:
                print(f"  - Path: {img[0]}")
                print(f"  - Label: {img[1]}")
        else:
            print("Gallery Images: None")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"ERROR: {e}")
print("\nDone.")
