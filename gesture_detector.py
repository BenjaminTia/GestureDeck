"""
Gesture Detector - Hand tracking and gesture recognition using MediaPipe.
Detects finger counts (0-10) and basic signs (fist, peace, OK, thumbs_up, point).
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os


class GestureDetector:
    """Detects hand gestures including finger counts and basic signs."""
    
    GESTURES = [
        'fist', 'one', 'two', 'three', 'four', 'five',
        'six', 'seven', 'eight', 'nine', 'ten',
        'peace', 'ok', 'thumbs_up', 'point'
    ]
    
    def __init__(self, model_path: str = None):
        """Initialize the gesture detector."""
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
        
        self.landmarker = self._create_landmarker(model_path)
        self.mp_draw = mp.solutions.drawing_utils if hasattr(mp, 'solutions') else None
        
    def _create_landmarker(self, model_path: str):
        """Create hand landmarker from model file."""
        if not os.path.exists(model_path):
            print(f"Warning: Model file not found: {model_path}")
            return None
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7
        )
        return vision.HandLandmarker.create_from_options(options)
    
    def detect(self, frame: np.ndarray) -> tuple:
        """
        Detect gestures in the frame.
        
        Returns:
            tuple: (gesture_name, confidence, landmarks_list, annotated_frame)
        """
        if not self.landmarker:
            return None, 0.0, [], frame
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        results = self.landmarker.detect(mp_image)
        
        gestures = []
        all_landmarks = []
        
        if results.hand_landmarks:
            for i, landmarks in enumerate(results.hand_landmarks):
                handedness = results.handedness[i] if results.handedness else None
                gesture, confidence = self._classify_gesture(landmarks, handedness)
                gestures.append((gesture, confidence))
                all_landmarks.append(landmarks)
        
        # Draw landmarks
        annotated = frame.copy()
        for landmarks in all_landmarks:
            self._draw_landmarks(annotated, landmarks)
        
        # Return primary gesture (first detected hand) or None
        if gestures:
            return gestures[0][0], gestures[0][1], all_landmarks, annotated
        
        return None, 0.0, [], annotated
    
    def _draw_landmarks(self, frame: np.ndarray, landmarks):
        """Draw hand landmarks on frame."""
        h, w, _ = frame.shape
        for landmark in landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
    
    def _classify_gesture(self, landmarks, handedness) -> tuple:
        """
        Classify gesture from landmarks.
        
        Returns:
            tuple: (gesture_name, confidence)
        """
        if not landmarks:
            return None, 0.0
        
        raised = self._count_raised_fingers(landmarks, handedness)
        
        # Check for specific signs first
        sign, sign_confidence = self._detect_sign(landmarks, handedness)
        
        if sign and sign_confidence > 0.7:
            return sign, sign_confidence
        
        # Fall back to finger count
        return self._finger_count_to_gesture(raised)
    
    def _count_raised_fingers(self, landmarks, handedness) -> int:
        """Count raised fingers (excluding thumb for signs)."""
        raised = 0
        
        # Thumb
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        wrist = landmarks[0]
        if abs(thumb_tip.x - wrist.x) > abs(thumb_ip.x - wrist.x):
            raised += 1
        
        # Index finger
        if landmarks[8].y < landmarks[6].y:
            raised += 1
        
        # Middle finger
        if landmarks[12].y < landmarks[10].y:
            raised += 1
        
        # Ring finger
        if landmarks[16].y < landmarks[14].y:
            raised += 1
        
        # Pinky
        if landmarks[20].y < landmarks[18].y:
            raised += 1
        
        return raised
    
    def _detect_sign(self, landmarks, handedness) -> tuple:
        """
        Detect specific hand signs (peace, ok, thumbs_up, point, fist).
        
        Returns:
            tuple: (sign_name or None, confidence)
        """
        is_right_hand = handedness and len(handedness) > 0 and handedness[0].category_name == 'Right'
        
        # Check for Peace sign (index and middle up, others down)
        if self._is_peace(landmarks, is_right_hand):
            return 'peace', 0.9
        
        # Check for OK sign (thumb and index touching, others up)
        if self._is_ok(landmarks):
            return 'ok', 0.85
        
        # Check for Thumbs Up (only thumb up, fist)
        if self._is_thumbs_up(landmarks, is_right_hand):
            return 'thumbs_up', 0.85
        
        # Check for Point (only index up)
        if self._is_point(landmarks, is_right_hand):
            return 'point', 0.85
        
        # Check for Fist (no fingers up)
        if self._is_fist(landmarks):
            return 'fist', 0.9
        
        return None, 0.0
    
    def _is_peace(self, landmarks, is_right_hand) -> bool:
        """Peace sign: index and middle up, ring and pinky down."""
        index_up = landmarks[8].y < landmarks[6].y
        middle_up = landmarks[12].y < landmarks[10].y
        ring_down = landmarks[16].y > landmarks[14].y
        pinky_down = landmarks[20].y > landmarks[18].y
        
        # Thumb should be somewhat down for peace
        thumb_tip = landmarks[4]
        thumb_base = landmarks[2]
        thumb_down = thumb_tip.y > thumb_base.y or abs(thumb_tip.x - thumb_base.x) < 0.05
        
        return index_up and middle_up and ring_down and pinky_down and thumb_down
    
    def _is_ok(self, landmarks) -> bool:
        """OK sign: thumb tip and index tip close together, others up."""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        # Distance between thumb and index tip
        distance = np.sqrt(
            (thumb_tip.x - index_tip.x) ** 2 + 
            (thumb_tip.y - index_tip.y) ** 2
        )
        
        # Other fingers should be up
        middle_up = landmarks[12].y < landmarks[10].y
        ring_up = landmarks[16].y < landmarks[14].y
        pinky_up = landmarks[20].y < landmarks[18].y
        
        return distance < 0.05 and middle_up and ring_up and pinky_up
    
    def _is_thumbs_up(self, landmarks, is_right_hand) -> bool:
        """Thumbs up: only thumb extended, others in fist."""
        # Thumb should be up
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        wrist = landmarks[0]
        thumb_up = abs(thumb_tip.x - wrist.x) > abs(thumb_ip.x - wrist.x)
        
        # All other fingers should be down (fist)
        index_down = landmarks[8].y > landmarks[6].y
        middle_down = landmarks[12].y > landmarks[10].y
        ring_down = landmarks[16].y > landmarks[14].y
        pinky_down = landmarks[20].y > landmarks[18].y
        
        return thumb_up and index_down and middle_down and ring_down and pinky_down
    
    def _is_point(self, landmarks, is_right_hand) -> bool:
        """Point: only index finger up, others down."""
        index_up = landmarks[8].y < landmarks[6].y
        middle_down = landmarks[12].y > landmarks[10].y
        ring_down = landmarks[16].y > landmarks[14].y
        pinky_down = landmarks[20].y > landmarks[18].y
        
        # Thumb should be somewhat across palm
        thumb_tip = landmarks[4]
        thumb_base = landmarks[2]
        thumb_across = thumb_tip.y > thumb_base.y
        
        return index_up and middle_down and ring_down and pinky_down and thumb_across
    
    def _is_fist(self, landmarks) -> bool:
        """Fist: all fingers curled down."""
        # All fingertips should be below their PIP joints
        index_down = landmarks[8].y > landmarks[6].y
        middle_down = landmarks[12].y > landmarks[10].y
        ring_down = landmarks[16].y > landmarks[14].y
        pinky_down = landmarks[20].y > landmarks[18].y
        
        # Thumb should be curled in
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_curled = thumb_tip.y > thumb_ip.y or abs(thumb_tip.x - thumb_ip.x) < 0.03
        
        return index_down and middle_down and ring_down and pinky_down and thumb_curled
    
    def _finger_count_to_gesture(self, count: int) -> tuple:
        """Convert finger count to gesture name."""
        gesture_map = {
            0: 'fist',
            1: 'one',
            2: 'two',
            3: 'three',
            4: 'four',
            5: 'five',
            6: 'six',
            7: 'seven',
            8: 'eight',
            9: 'nine',
            10: 'ten'
        }
        return gesture_map.get(count, 'fist'), 0.8


if __name__ == '__main__':
    # Test the detector
    detector = GestureDetector()
    cap = cv2.VideoCapture(0)
    
    print("Gesture Detector Test - Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        gesture, confidence, landmarks, annotated = detector.detect(frame)
        
        if gesture:
            cv2.putText(annotated, f"Gesture: {gesture} ({confidence:.2f})", 
                       (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        cv2.imshow("Gesture Detector", annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
