from ultralytics import YOLO

def load_model(model_path="model/exam/yolov9m.pt"):
    return YOLO(model_path)
