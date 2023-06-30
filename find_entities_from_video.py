import cv2
import concurrent.futures

def detect_objects(frame, cascade):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    objects = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(objects)

def count_objects(video_path, skip_factor=10):
    # Load the pre-trained classifiers for cars, pedestrians, bicycles, and motorbikes
    car_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_car.xml')
    pedestrian_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
    bicycle_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_bicycle.xml')
    motorbike_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_motorbike.xml')

    # Open the video file
    video = cv2.VideoCapture(video_path)

    car_count = 0
    pedestrian_count = 0
    bicycle_count = 0
    motorbike_count = 0
    frame_count = 0

    # Read the video frame by frame
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        # Skip frames based on the skip factor
        if frame_count % skip_factor != 0:
            frame_count += 1
            continue

        # Resize the frame for faster processing
        resized_frame = cv2.resize(frame, None, fx=0.5, fy=0.5)

        # Create a thread pool for parallel processing of object detection
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            # Submit object detection tasks for each cascade classifier
            futures.append(executor.submit(detect_objects, resized_frame, car_cascade))
            futures.append(executor.submit(detect_objects, resized_frame, pedestrian_cascade))
            futures.append(executor.submit(detect_objects, resized_frame, bicycle_cascade))
            futures.append(executor.submit(detect_objects, resized_frame, motorbike_cascade))

            # Wait for the tasks to complete and retrieve the results
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if cascade == car_cascade:
                    car_count += result
                elif cascade == pedestrian_cascade:
                    pedestrian_count += result
                elif cascade == bicycle_cascade:
                    bicycle_count += result
                elif cascade == motorbike_cascade:
                    motorbike_count += result

        frame_count += 1

    # Release the video capture
    video.release()

    # Print the counts of cars, pedestrians, bicycles, and motorbikes
    print('Number of cars:', car_count)
    print('Number of pedestrians:', pedestrian_count)
    print('Number of bicycles:', bicycle_count)
    print('Number of motorbikes:', motorbike_count)

# Provide the path to the video file
video_path = 'path/to/your/video/file.mp4'

# Specify the skip factor (optional, default is 10)
skip_factor = 10

# Call the function to count objects in the video
count_objects(video_path, skip_factor)
