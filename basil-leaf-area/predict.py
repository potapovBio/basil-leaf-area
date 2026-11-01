"""Measure visible projected area using custom YOLO segmentation weights."""
import argparse
import json
from pathlib import Path
from calibration import area_cm2


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('--weights', type=Path, required=True)
    p.add_argument('--field-width', type=float, required=True, help='Field width at reference plane, cm')
    p.add_argument('--field-height', type=float, required=True, help='Field height at reference plane, cm')
    p.add_argument('--distance', type=float, help='Current distance, cm; manual input')
    p.add_argument('--reference-distance', type=float, help='Distance at calibration, cm')
    p.add_argument('--output', type=Path, default=Path('outputs/prediction.jpg'))
    p.add_argument('--conf', type=float, default=0.25)
    p.add_argument('--imgsz', type=int, default=640)
    p.add_argument('--device', default='cpu')
    a = p.parse_args()
    try:
        area_cm2(0, 1, 1, a.field_width, a.field_height, a.distance, a.reference_distance)
    except ValueError as e:
        p.error(str(e))
    if not 0 < a.conf <= 1 or a.imgsz <= 0:
        p.error('conf must be in (0, 1]; imgsz must be positive')
    if a.output.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
        p.error('output must be JPG or PNG')
    outputs = [a.output, a.output.with_suffix('.json')]
    if any(o.resolve() in {a.image.resolve(), a.weights.resolve()} for o in outputs):
        p.error('output must not overwrite image or weights')
    if not a.image.is_file() or not a.weights.is_file():
        p.error('image and custom weights must exist locally')
    import cv2
    import numpy as np
    from ultralytics import YOLO
    img = cv2.imread(str(a.image))
    if img is None:
        p.error('could not read image')
    h, w = img.shape[:2]
    model = YOLO(str(a.weights))
    if model.task != 'segment':
        p.error('segmentation weights are required')
    result = model.predict(img, conf=a.conf, imgsz=a.imgsz, device=a.device,
                           retina_masks=True, verbose=False)[0]
    objects = []
    if result.masks is not None:
        for i, mask in enumerate(result.masks.data.cpu().numpy()):
            if mask.shape != (h, w):
                raise RuntimeError('Mask/image size mismatch; refusing uncalibrated resize')
            binary = (mask > 0.5).astype(np.uint8)
            pixels = int(np.count_nonzero(binary))
            area = area_cm2(pixels, w, h, a.field_width, a.field_height,
                            a.distance, a.reference_distance)
            cls = int(result.boxes.cls[i].item())
            objects.append({'id': i + 1, 'class': result.names[cls],
                            'confidence': float(result.boxes.conf[i].item()),
                            'pixels': pixels, 'projected_area_cm2': area})
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img, contours, -1, (0, 0, 255), max(1, w // 500))
            x, y = map(int, result.boxes.xyxy[i][:2].cpu().tolist())
            cv2.putText(img, f'{i+1}: {area:.2f} cm2', (x, max(25, y)),
                        cv2.FONT_HERSHEY_SIMPLEX, max(0.5, w / 1600), (0, 0, 255), 2)
    report = {'image': a.image.name, 'weights': a.weights.name,
              'image_width': w, 'image_height': h,
              'calibration': {'field_width_cm': a.field_width, 'field_height_cm': a.field_height,
                              'distance_cm': a.distance, 'reference_distance_cm': a.reference_distance},
              'objects': objects, 'count': len(objects),
              'sum_projected_area_cm2': sum(o['projected_area_cm2'] for o in objects)}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(a.output), img):
        raise OSError(f'Could not save {a.output}')
    a.output.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
