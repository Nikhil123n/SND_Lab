import time

def pre(pipeline):
    print("[Pipeline] Preprocessing...")
    time.sleep(20)  

def sort(pipeline):
    print(f"[Pipeline] Sorting with ...")
    time.sleep(20) 

def post(pipeline):
    print("[Pipeline] Postprocessing...")
    time.sleep(10)  

def export(pipeline):
    print("[Pipeline] Exporting results...")
