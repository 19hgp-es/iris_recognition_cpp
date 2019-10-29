import cv2 as cv
import math
import numpy as np
import os
import time

# filepath1 = "CASIA-IrisV4(JPG)/"
# filepath2 = "CASIA-Iris-Syn"

filepath1 = "MMU_Iris/"
filepath2 = "MMU_Iris_Database"

input_img_path = "/Users/leejonguk/Desktop/hanyang/project/iris/"+filepath1+filepath2
output_path = "/Users/leejonguk/Desktop/grad_proj/norm_imgs_bmp/"+filepath1+filepath2

# lists and distionaries for preprocessing
inner_circle_rad_list = list()
outer_circle_rad_list = list()
inner_circle_rad_dict = dict()
outer_circle_rad_dict = dict()

# database name : (pupil_min, pupil_max, iris_min, iris_max, iris_rad_val)
databases = {   "MMU_Iris_Database"   : (15, 40,  35, 60 , 56),
				"CASIA-Iris-Distance" : (20, 100, 40, 140, 100), 
				"CASIA-Iris-Interval" : (20, 100, 40, 140, 100),
				"CASIA-Iris-Lamp"     : (15, 60,  35, 100, 100),
				"CASIA-Iris-Syn"      : (20, 60,  40, 140, 85),
				"CASIA-Iris-Thousand" : (20, 60,  40, 100, 82),
				"CASIA-Iris-Twins"    : (20, 100, 40, 140, 100)}

# global variables
iris_circle = [0, 0, 0]
inner_temp = [0, 0, 0]


def bottom_hat_median_blurr(image):
    cimg = image
    
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    blackhat = cv.morphologyEx(cimg, cv.MORPH_BLACKHAT, kernel)
    bottom_hat_filtered = cv.add(blackhat, cimg)
    
    return cv.medianBlur(bottom_hat_filtered, 17)


def adjust_gamma(image, gamma=1.0):
    inv_gamma = 1.0 / gamma
    table = np.array(
    	[ ((i / 255.0) ** inv_gamma) * 255
		for i in np.arange(0, 256)]).astype("uint8")

    return cv.LUT(image, table)


def detect_circles(img, canny_param=20, hough_param=20):
    global inner_circle_rad_list, outer_circle_rad_list, inner_temp
    global iris_circle

    filtered = bottom_hat_median_blurr(img)
    adjusted = adjust_gamma(filtered, 10)
    
    circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
    								param1 = canny_param,
    								param2 = hough_param,
    								minRadius = databases[filepath2][0],
    								maxRadius = databases[filepath2][1])

    inner_circle = [0, 0, 0]
    if circles is not None:
    	inner_circle = np.uint16(np.around(circles[0][0])).tolist()

    circle_frame = cv.circle(img, (inner_circle[0], inner_circle[1]), 
    					inner_circle[2], (0,0,0), cv.FILLED)
    
    inner_circle_rad_list.append(inner_circle[2])
    inner_temp = inner_circle

    if inner_circle[2] in inner_circle_rad_dict:
    	inner_circle_rad_dict[inner_circle[2]] += 1
    else:
    	inner_circle_rad_dict[inner_circle[2]] = 1

    circles = circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
									param1=canny_param,
									param2=hough_param,
									minRadius=databases[filepath2][2],
									maxRadius=databases[filepath2][3])

    outer_circle = [0, 0, 0]
    if circles is not None:
    	for circle in circles[0]:
    		outer_circle = np.uint16(np.around(circle)).tolist()
    		if (abs(outer_circle[0] - inner_circle[0]) < 15) and (abs(outer_circle[1] - inner_circle[1]) < 15):
		    	outer_circle_rad_list.append(outer_circle[2])
		    	if outer_circle[2] in outer_circle_rad_dict:
		    		outer_circle_rad_dict[outer_circle[2]] += 1
		    	else:
		    		outer_circle_rad_dict[outer_circle[2]] = 1
    			break

    outer_circle[0], outer_circle[1] = inner_circle[0], inner_circle[1]
    outer_circle[2] = databases[filepath2][4]

    iris_circle = outer_circle

    return circle_frame


def detect_iris_frame(frame):
	global iris_circle

	if iris_circle[0] < iris_circle[2]:
		iris_circle[2] = iris_circle[0]
	if iris_circle[1] < iris_circle[2]:
		iris_circle[2] = iris_circle[1]
	if frame.shape[0] - iris_circle[1] < iris_circle[2]:
		iris_circle[2] = frame.shape[0] - iris_circle[1]
	if frame.shape[1] - iris_circle[0] < iris_circle[2]:
		iris_circle[2] = frame.shape[1] - iris_circle[0]

	mask = cv.bitwise_not(cv.circle(np.zeros((np.size(frame,0),np.size(frame,1),1), np.uint8)
					, (iris_circle[0], iris_circle[1]), iris_circle[2], (255,255,255), cv.FILLED))
	

	iris_frame = frame.copy()
	iris_frame = cv.subtract(frame, frame, iris_frame, mask, -1)

	iris_frame = iris_frame[(iris_circle[1] - iris_circle[2]):(iris_circle[1] + iris_circle[2]),
						(iris_circle[0] - iris_circle[2]):(iris_circle[0] + iris_circle[2])]

	return iris_frame

def getPolar2CartImg(image, rad):
	c = (float(np.size(image, 0)/2.0), float(np.size(image, 1)/2.0))
	imgRes = cv.warpPolar(image, (rad*3,360), c, np.size(image, 0)/2, cv.WARP_POLAR_LOG)

	for valid_width in reversed(range(rad*3)):
		blank_cnt = 0
		for h in range(360):
			if (imgRes[h][valid_width] != 0):
				blank_cnt+=1
		if(blank_cnt == 0):
			imgRes = imgRes[0:360, valid_width:rad*3]
			break

	imgRes = cv.resize(imgRes, (80, 360), interpolation=cv.INTER_CUBIC)
	

	return imgRes

def main():
	startTime = time.time()

	key = 0

	error_list = list()

	total_pic = 0
	for (path, dir, files) in os.walk(input_img_path):
		if not(os.path.isdir(output_path+ path.split(filepath2)[1])):
			os.mkdir(output_path +path.split(filepath2)[1])
		for filename in files:
			ext = os.path.splitext(filename)[-1]
			if ((ext == '.bmp') or (ext == '.jpg')):
				total_pic += 1
				frame = cv.imread(path + "/" + filename, cv.CV_8UC1)
				temp = frame.copy()
				output = frame.copy()
				circle = detect_circles(frame)
			
				iris = detect_iris_frame(circle)

				try:
					norm_frame = getPolar2CartImg(iris,iris_circle[2])

				except cv.error:
					print("cv2 error detected..")
					error_list.append(filename)
					continue

				cv.circle(temp, (iris_circle[0], iris_circle[1]), 
	    					iris_circle[2], (255,255,255), 4)
				cv.circle(temp, (inner_temp[0], inner_temp[1]),
							inner_temp[2], (255,255,255), 4)

				cv.imshow("input", temp)
				cv.imshow("iris",circle)
				cv.imshow("iris",output)
				cv.imshow("iris_",iris)
				cv.imshow("normalized", norm_frame)


				# if (iris_circle[2] - inner_temp[2] < 10):
				# 	cv.waitKey(100000)
				# 	err_list.append(filename)
				# 	print("error1")

				# cv.imwrite(output_path + path.split(filepath2)[1] + "/" + filename[:-4] + '.bmp', norm_frame)

				# key = cv.waitKey(100000)
				key = cv.waitKey(1)
				if (key == 27 or key == 1048603):
					break	

	endTime = time.time() - startTime
	print("processing time : " + str(endTime))

	inner_circle_rad_list.sort()
	outer_circle_rad_list.sort()

	print("total pictures : " + str(total_pic))
	if len(inner_circle_rad_list) != 0:
		print("inner_circle_avg : " +  str(sum(inner_circle_rad_list)) + " / " + str(len(inner_circle_rad_list)) + " = " + str(sum(inner_circle_rad_list) / len(inner_circle_rad_list)))
		print("inner_circle min_val : " + str(inner_circle_rad_list[0]))
		print("inner_circle max_val : " + str(inner_circle_rad_list[-1]))
		print()

	if len(outer_circle_rad_list) != 0:
		print("outer_circle_avg : " +  str(sum(outer_circle_rad_list)) + " / " + str(len(outer_circle_rad_list)) + " = " + str(sum(outer_circle_rad_list) / len(outer_circle_rad_list)))
		print("outer_circle min_val : " + str(outer_circle_rad_list[0]))
		print("outer_circle max_val : " + str(outer_circle_rad_list[-1]))
		print()

	inner_circle_rad_list.sort()
	outer_circle_rad_list.sort()

	inner_key = list(inner_circle_rad_dict.keys())
	outer_key = list(outer_circle_rad_dict.keys())
	inner_key.sort()
	outer_key.sort()

	for item in inner_key:
		print(str(item) + " : " + str(inner_circle_rad_dict[item]))

	for item in outer_key:
		print(str(item) + " : " + str(outer_circle_rad_dict[item]))



	# write data
	with open(output_path + '/error_file.txt', 'w') as file:
		file.write("execution time : " + str(endTime) + "\n\n")
		file.write("number of pictures : " + str(total_pic) + "\n\n")
		file.write("inner_circle_avg : " +  str(sum(inner_circle_rad_list)) + " / " + str(len(inner_circle_rad_list)) + " = " + str(sum(inner_circle_rad_list) / len(inner_circle_rad_list)) + "\n")
		file.write("inner_circle min_val : " + str(inner_circle_rad_list[0]) + "\n")
		file.write("inner_circle_max_val : " + str(inner_circle_rad_list[-1]) + "\n")
		
		file.write("inner_circle_radius values\n\n")
		for item in inner_key:
			file.write(str(item) + " : " + str(inner_circle_rad_dict[item]) + "\n")

		file.write("outer_circle_radius values\n\n")
		for item in outer_key:
			file.write(str(item) + " : " + str(outer_circle_rad_dict[item]) + "\n")



		file.write("outer_circle_avg : " +  str(sum(outer_circle_rad_list)) + " / " + str(len(outer_circle_rad_list)) + " = " + str(sum(outer_circle_rad_list) / len(outer_circle_rad_list)) + "\n")
		file.write("outer_circle min_val : " + str(outer_circle_rad_list[0]) + "\n")
		file.write("outer_circle_max_val : " + str(outer_circle_rad_list[-1]) + "\n")
		
	cv.destroyAllWindows()


if __name__ == "__main__":
	main()