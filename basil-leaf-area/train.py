"""Train the basil or model-system segmentation model with explicitly selected initial weights."""
import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=['basil', 'cubes'], required=True)
    p.add_argument('--data', type=Path, help='YOLO-seg dataset YAML; overrides stage config')
    p.add_argument('--model', required=True, help='YOLO11-seg initial weights: local path or model name')
    p.add_argument('--epochs', type=int)
    p.add_argument('--device', default='cpu')
    a = p.parse_args()
    epochs = a.epochs if a.epochs is not None else (25 if a.stage == 'basil' else 50)
    if epochs <= 0:
        p.error('epochs must be positive')
    data = a.data or Path('configs') / f'{a.stage}.yaml'
    if not data.is_file():
        p.error(f'dataset configuration does not exist: {data}')
    from ultralytics import YOLO
    YOLO(a.model).train(data=str(data), epochs=epochs, imgsz=640, batch=8,
                        patience=200, seed=0, device=a.device,
                        project='runs/segment', name=a.stage)


if __name__ == '__main__':
    main()
