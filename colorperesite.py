import cv2
import numpy as np
import math
from typing import List, Tuple

global img
HSV_LOW_BOUND = np.array([0, 0, 0])
HSV_HIGH_BOUND = np.array([255, 255, 255])
NEXT = 0
PREVIOUS = 1
FIRST_CHILD = 2
PARENT = 3

def find_largest_contour_and_child(contours: List[np.ndarray], hierarchy: List[np.ndarray]) -> Tuple[int, int]:
    """Find the largest contour index and his child index

    Args:
        contours (list[np.ndarray]): The countours list
        hierarchy (list[np.ndarray]): The respective heirarchy list

    Returns:
        (int, int): the indexes of the largest contour and his child
    """
    largest_contour_index = max(range(len(contours)), key=lambda i: cv2.contourArea(contours[i]))
    child_index = hierarchy[largest_contour_index][FIRST_CHILD]
    biggest_child_contour_index = -1
    biggest_child_contour_area = 0
    while child_index != -1:
        child_contour = contours[child_index]
        child_contour_area = cv2.contourArea(child_contour)
        if child_contour_area > biggest_child_contour_area:
            biggest_child_contour_area = child_contour_area
            biggest_child_contour_index = child_index
        child_index = hierarchy[child_index][NEXT]
    return (largest_contour_index, biggest_child_contour_index)

def get_hsv_values(img, x, y):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv = hsv[y, x]
    return hsv

def expand_hsv_bounds(img, contour, hsv_low_bound, hsv_high_bound, neighborhood_size=5, tolerance=10, mouse_points=None):
    """
    Expand the HSV value bounds based on the pixels in the contours, their neighborhood, and additional mouse points.

    Args:
        img (np.ndarray): The input image.
        contour (np.ndarray): A contour representing the region of interest.
        hsv_low_bound (np.ndarray): The current lower HSV bound.
        hsv_high_bound (np.ndarray): The current upper HSV bound.
        neighborhood_size (int): The size of the neighborhood around each contour pixel.
        tolerance (int): The tolerance value for including neighboring pixels in the bounds.
        mouse_points (list): A list of (x, y) coordinates from mouse clicks.

    Returns:
        tuple: A tuple containing the updated HSV low and high bounds.
    """
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    updated_low_bound = hsv_low_bound.copy()
    updated_high_bound = hsv_high_bound.copy()

    for pixel in contour:
        x, y = pixel[0]
        for neighbor_x in range(max(0, x - neighborhood_size // 2), min(img.shape[1], x + neighborhood_size // 2 + 1)):
            for neighbor_y in range(max(0, y - neighborhood_size // 2), min(img.shape[0], y + neighborhood_size // 2 + 1)):
                neighbor_hsv = hsv_img[neighbor_y, neighbor_x]
                if np.all(np.abs(neighbor_hsv - hsv_low_bound) <= tolerance) or np.all(np.abs(neighbor_hsv - hsv_high_bound) <= tolerance):
                    updated_low_bound = np.minimum(updated_low_bound, neighbor_hsv - tolerance)
                    updated_high_bound = np.maximum(updated_high_bound, neighbor_hsv + tolerance)


    return updated_low_bound, updated_high_bound

# Click event
def click_event(event, x, y, flags, params):
    # Left click
    if event == cv2.EVENT_LBUTTONDOWN:
        print(x, ' ', y)
        hsv = get_hsv_values(img, x, y)
        global HSV_LOW_BOUND, HSV_HIGH_BOUND
        HSV_LOW_BOUND = np.array([hsv[0], hsv[1], hsv[2]])
        HSV_HIGH_BOUND = np.array([hsv[0], hsv[1], hsv[2]])

while (1):
    img = cv2.imread('colorperesite.PNG')
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Create a mask based on the specified HSV color range
    mask = cv2.inRange(hsv, HSV_LOW_BOUND, HSV_HIGH_BOUND)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    

    # Draw all contours on the original image
    #cv2.drawContours(img, contours, -1, (255, 0, 255), 3)

    if len(contours) != 0:
        hierarchy = hierarchy[0]
        # Find the largest contour and child contour within the largest contour
        largest_contour_index, biggest_child_contour_index = find_largest_contour_and_child(contours, hierarchy)
        HSV_LOW_BOUND, HSV_HIGH_BOUND = expand_hsv_bounds(img, contours[largest_contour_index], HSV_LOW_BOUND, HSV_HIGH_BOUND)
        HSV_LOW_BOUND, HSV_HIGH_BOUND = expand_hsv_bounds(img, contours[biggest_child_contour_index], HSV_LOW_BOUND, HSV_HIGH_BOUND)
        #cv2.drawContours(image, contours, largest_contour_index, (255, 0, 0), 5)
        # Draw the largest child contour
        if biggest_child_contour_index != -1:
            biggest_child_contour = contours[biggest_child_contour_index]
            #cv2.drawContours(image, [biggest_child_contour], 0, (0, 255, 0), 2)

            outer_contour = contours[largest_contour_index]
            inner_contour = contours[biggest_child_contour_index]

            # Check if both outer and inner contours have areas greater than 3600
            if (cv2.contourArea(outer_contour) > 100) and (cv2.contourArea(inner_contour) > 100):
                x, y, w, h = cv2.boundingRect(outer_contour)
                outer_aspect_ratio = float(w) / h
                outer_center = (int(x+(w/2)), int(y+(h/2)))
                cv2.circle(img, outer_center, 10, (255,255,255),-3)
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 5)

                x1, y1, w1, h1 = cv2.boundingRect(inner_contour)
                inner_aspect_ratio = float(w1) / h1
                inner_center = (int(x1+(w1/2)), int(y1+(h1/2)))
                cv2.circle(img, inner_center, 5, (0,0,0),-3)
                cv2.rectangle(img, (x1, y1), (x1+w1, y1+h1), (255, 0, 0), 5)
            
                # Check if the aspect ratios and distance between centers meet the criteria
                if (abs(outer_aspect_ratio - inner_aspect_ratio) < 10) and (math.dist(outer_center, inner_center) < 20):
                    img = cv2.putText(img, 'probably donut?☺☻♥', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2, cv2.LINE_AA)
                    
                else:
                    cv2.putText(img, 'coected note pls bump to seperate', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)

        else:
            cv2.putText(img, 'There is no child contour :(', (0, 0), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)


    cv2.imshow("img", img)
    cv2.imshow("mask", mask)

    cv2.setMouseCallback('img', click_event)

    # Check for key press to exit
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        break
print (HSV_LOW_BOUND)
print(HSV_HIGH_BOUND)
cv2.destroyAllWindows()