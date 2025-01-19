import streamlit as st
import cv2
import mediapipe as mp
import pyautogui
import time
import threading

# Initialize mediapipe hands module
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hand_obj = mp_hands.Hands(max_num_hands=1)

# Function to count the number of fingers based on landmark positions
def count_fingers(lst):
    count = 0
    threshold = (lst.landmark[0].y * 100 - lst.landmark[9].y * 100) / 2

    if (lst.landmark[5].y * 100 - lst.landmark[8].y * 100) > threshold:
        count += 1
    if (lst.landmark[9].y * 100 - lst.landmark[12].y * 100) > threshold:
        count += 1
    if (lst.landmark[13].y * 100 - lst.landmark[16].y * 100) > threshold:
        count += 1
    if (lst.landmark[17].y * 100 - lst.landmark[20].y * 100) > threshold:
        count += 1
    if (lst.landmark[5].x * 100 - lst.landmark[4].x * 100) > 6:
        count += 1

    return count

# Task description table
task_descriptions = {
    1: "Forward Skip - Go to the next item or slide",
    2: "Backward Skip - Go to the previous item or slide",
    3: "Volume Up - Increase the volume",
    4: "Volume Down - Decrease the volume",
    5: "Pause/Play - Toggle play/pause"
}

# Function to handle video stream and gesture recognition
def run_camera(stop_flag):
    cap = cv2.VideoCapture(0)
    prev = -1
    task_text = ""  # Initialize task text

    start_init = False
    while not stop_flag.is_set():
        end_time = time.time()
        _, frm = cap.read()
        frm = cv2.flip(frm, 1)

        # Process the frame with mediapipe hands
        res = hand_obj.process(cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))

        if res.multi_hand_landmarks:
            hand_keyPoints = res.multi_hand_landmarks[0]
            finger_count = count_fingers(hand_keyPoints)

            if not (prev == finger_count):
                if not (start_init):
                    start_time = time.time()
                    start_init = True
                elif (end_time - start_time) > 0.2:
                    if finger_count == 1:
                        pyautogui.press("right")
                        task_text = "Forward Skip"
                    elif finger_count == 2:
                        pyautogui.press("left")
                        task_text = "Backward Skip"
                    elif finger_count == 3:
                        pyautogui.press("volumeup")
                        task_text = "Volume Up"
                    elif finger_count == 4:
                        pyautogui.press("volumedown")
                        task_text = "Volume Down"
                    elif finger_count == 5:
                        pyautogui.press("space")
                        task_text = "Pause/Play"

                    prev = finger_count
                    start_init = False

            mp_drawing.draw_landmarks(frm, hand_keyPoints, mp_hands.HAND_CONNECTIONS)

        # Draw task text inside a box
        cv2.rectangle(frm, (10, 10), (300, 60), (0, 0, 0), -1)  # Draw a filled black rectangle
        cv2.putText(frm, task_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Display the frame with task information
        cv2.imshow("Hand Gesture Control", frm)

        # Exit the webcam on pressing the 'Esc' key
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# Initialize session state variables
if "stop_camera" not in st.session_state:
    st.session_state.stop_camera = threading.Event()

# Streamlit interface
st.title("Hand Gesture Control App")

st.markdown("""
    This app uses hand gestures to control different actions such as controlling media volume, skipping slides, and playing/pausing content. 
    The following gestures are recognized:
""")

# Display a table of gestures
gesture_data = {
    "Gesture": ["1 Finger", "2 Fingers", "3 Fingers", "4 Fingers", "5 Fingers"],
    "Action": ["Forward Skip", "Backward Skip", "Volume Up", "Volume Down", "Pause/Play"]
}

st.table(gesture_data)

# Start button for camera feed
if st.button("Start Gesture Control"):
    st.session_state.stop_camera.clear()  # Clear the stop event
    st.write("Starting camera feed...")

    # Start the gesture recognition in a separate thread
    camera_thread = threading.Thread(target=run_camera, args=(st.session_state.stop_camera,))
    camera_thread.daemon = True
    camera_thread.start()

    st.write("Perform gestures in front of the camera.")

# Stop button for camera feed
if st.button("Stop Gesture Control"):
    st.write("Stopping camera feed...")
    st.session_state.stop_camera.set()  # Set the stop event to terminate the camera thread